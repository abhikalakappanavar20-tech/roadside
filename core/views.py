from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from api.models import UserProfile, ServiceRequest, ServiceHistory
from api.forms import CustomerRegistrationForm, ProviderRegistrationForm
from api.blob_storage import upload_file, delete_file


# ==================== Home & Auth Views ====================


def home(request):
    """Landing page with role selection"""
    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "core/home.html")


def customer_register(request):
    """Customer registration view"""
    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("customer_login")
    else:
        form = CustomerRegistrationForm()

    return render(request, "core/customer_register.html", {"form": form})


def provider_register(request):
    """Provider registration view"""
    if request.method == "POST":
        form = ProviderRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, "Provider account created successfully! Please log in."
            )
            return redirect("provider_login")
    else:
        form = ProviderRegistrationForm()

    return render(request, "core/provider_register.html", {"form": form})


def customer_login(request):
    """Customer login view"""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Verify it's a customer
            if user.profile.role != "customer":
                messages.error(
                    request, "Please use the provider login for provider accounts."
                )
                return redirect("provider_login")

            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect("customer_dashboard")
    else:
        form = AuthenticationForm()

    return render(request, "core/customer_login.html", {"form": form})


def provider_login(request):
    """Provider login view"""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Verify it's a provider
            if user.profile.role != "provider":
                messages.error(
                    request, "Please use the customer login for customer accounts."
                )
                return redirect("customer_login")

            login(request, user)

            # Update provider availability
            user.profile.is_available = True
            user.profile.save()

            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect("provider_dashboard")
    else:
        form = AuthenticationForm()

    return render(request, "core/provider_login.html", {"form": form})


def logout_view(request):
    """Logout view"""
    if request.user.is_authenticated and request.user.profile.role == "provider":
        # Set provider as unavailable
        request.user.profile.is_available = False
        request.user.profile.save()

    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("home")


# ==================== Dashboard Views ====================


@login_required
def dashboard(request):
    """Main dashboard - redirects based on role"""
    role = request.user.profile.role

    if role == "customer":
        return redirect("customer_dashboard")
    elif role == "provider":
        return redirect("provider_dashboard")
    elif role == "admin":
        return redirect("admin_dashboard")
    else:
        return redirect("home")


@login_required
def customer_dashboard(request):
    """Customer dashboard - shows service requests and new request form"""
    user_requests = ServiceRequest.objects.filter(user=request.user).order_by(
        "-created_at"
    )[:10]

    active_request = ServiceRequest.objects.filter(
        user=request.user, status__in=["pending", "accepted", "in_progress"]
    ).first()

    context = {
        "active_request": active_request,
        "recent_requests": user_requests,
    }
    return render(request, "core/customer_dashboard.html", context)


@login_required
def provider_dashboard(request):
    """Provider dashboard - shows available and assigned requests"""
    profile = request.user.profile

    # Get provider's active requests
    my_active_requests = ServiceRequest.objects.filter(
        assigned_provider=request.user, status__in=["accepted", "in_progress"]
    ).order_by("-accepted_at")

    # Get provider's recent requests (all statuses)
    my_recent_requests = ServiceRequest.objects.filter(
        assigned_provider=request.user
    ).order_by("-created_at")[:10]

    # Calculate earnings (completed requests)
    completed_count = ServiceRequest.objects.filter(
        assigned_provider=request.user, status="paid"
    ).count()

    context = {
        "profile": profile,
        "my_active_requests": my_active_requests,
        "my_recent_requests": my_recent_requests,
        "completed_count": completed_count,
    }
    return render(request, "core/provider_dashboard.html", context)


@login_required
def admin_dashboard(request):
    """Admin dashboard - overview of all requests and providers"""
    if request.user.profile.role != "admin":
        messages.error(request, "Access denied.")
        return redirect("home")

    # Get stats
    total_requests = ServiceRequest.objects.count()
    pending_requests = ServiceRequest.objects.filter(status="pending").count()
    active_requests = ServiceRequest.objects.filter(
        status__in=["accepted", "in_progress"]
    ).count()
    completed_requests = ServiceRequest.objects.filter(status="paid").count()

    total_providers = UserProfile.objects.filter(role="provider").count()
    active_providers = UserProfile.objects.filter(
        role="provider", is_available=True
    ).count()

    total_customers = UserProfile.objects.filter(role="customer").count()

    # Recent requests
    recent_requests = ServiceRequest.objects.all().order_by("-created_at")[:20]

    # All providers
    providers = UserProfile.objects.filter(role="provider").select_related("user")

    context = {
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "active_requests": active_requests,
        "completed_requests": completed_requests,
        "total_providers": total_providers,
        "active_providers": active_providers,
        "total_customers": total_customers,
        "recent_requests": recent_requests,
        "providers": providers,
    }
    return render(request, "core/admin_dashboard.html", context)


# ==================== Service Request Views ====================


@login_required
def new_request(request):
    """Create a new service request"""
    if request.user.profile.role != "customer":
        messages.error(request, "Only customers can create service requests.")
        return redirect("dashboard")

    if request.method == "POST":
        service_type = request.POST.get("service_type")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        address = request.POST.get("address", "")
        description = request.POST.get("description", "")

        if not all([service_type, latitude, longitude]):
            messages.error(
                request, "Please enable location access and select a service type."
            )
            return redirect("new_request")

        # Create the service request
        service_request = ServiceRequest.objects.create(
            user=request.user,
            service_type=service_type,
            location_lat=latitude,
            location_long=longitude,
            location_address=address,
            issue_description=description,
            status="pending",
        )

        messages.success(
            request,
            f"Service request {service_request.request_id} created successfully!",
        )
        return redirect("customer_dashboard")

    return render(request, "core/new_request.html")


@login_required
def accept_request(request, request_id):
    """Provider accepts a service request"""
    if request.user.profile.role != "provider":
        messages.error(request, "Only providers can accept requests.")
        return redirect("dashboard")

    service_request = get_object_or_404(ServiceRequest, id=request_id)

    # Check if request is still available
    if service_request.status != "pending":
        messages.warning(request, "This request is no longer available.")
        return redirect("provider_dashboard")

    # Check if provider can handle this service type
    profile = request.user.profile
    if service_request.service_type == "fuel" and not profile.can_provide_fuel:
        messages.error(request, "You are not authorized to provide fuel services.")
        return redirect("provider_dashboard")

    if service_request.service_type != "fuel" and not profile.can_provide_mechanic:
        messages.error(request, "You are not authorized to provide mechanic services.")
        return redirect("provider_dashboard")

    # Accept the request
    service_request.status = "accepted"
    service_request.assigned_provider = request.user
    service_request.accepted_at = timezone.now()
    service_request.save()

    messages.success(
        request, f"You have accepted request {service_request.request_id}!"
    )
    return redirect("request_detail", request_id=service_request.request_id)


@login_required
def request_detail(request, request_id):
    """View details of a specific service request"""
    service_request = get_object_or_404(ServiceRequest, request_id=request_id)

    # Check permissions
    if (
        request.user.profile.role == "customer" and service_request.user != request.user
    ) or (
        request.user.profile.role == "provider"
        and service_request.assigned_provider != request.user
    ):
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    # Safely get service history (may not exist)
    try:
        history = ServiceHistory.objects.get(service_request=service_request)
    except ServiceHistory.DoesNotExist:
        history = None

    context = {
        "service_request": service_request,
        "history": history,
    }
    return render(request, "core/request_detail.html", context)


@login_required
def start_service(request, request_id):
    """Provider starts the service"""
    if request.user.profile.role != "provider":
        messages.error(request, "Only providers can start services.")
        return redirect("dashboard")

    service_request = get_object_or_404(ServiceRequest, request_id=request_id)

    if service_request.assigned_provider != request.user:
        messages.error(request, "This is not your request.")
        return redirect("dashboard")

    if service_request.status != "accepted":
        messages.warning(request, "Request must be accepted first.")
        return redirect("request_detail", request_id=request_id)

    service_request.status = "in_progress"
    service_request.started_at = timezone.now()
    service_request.save()

    messages.success(request, "Service marked as in progress!")
    return redirect("request_detail", request_id=request_id)


@login_required
def complete_service(request, request_id):
    """Provider completes the service"""
    if request.user.profile.role != "provider":
        messages.error(request, "Only providers can complete services.")
        return redirect("dashboard")

    service_request = get_object_or_404(ServiceRequest, request_id=request_id)

    if service_request.assigned_provider != request.user:
        messages.error(request, "This is not your request.")
        return redirect("dashboard")

    if service_request.status != "in_progress":
        messages.warning(request, "Request must be in progress first.")
        return redirect("request_detail", request_id=request_id)

    service_request.status = "completed"
    service_request.completed_at = timezone.now()
    service_request.save()

    messages.success(
        request, "Service completed! Waiting for customer payment confirmation."
    )
    return redirect("request_detail", request_id=request_id)


@login_required
def payment_page(request, request_id):
    """Show payment options page"""
    if request.user.profile.role != "customer":
        messages.error(request, "Only customers can make payments.")
        return redirect("dashboard")

    service_request = get_object_or_404(ServiceRequest, request_id=request_id)

    if service_request.user != request.user:
        messages.error(request, "This is not your request.")
        return redirect("dashboard")

    if service_request.status != "completed":
        messages.warning(request, "Service must be completed first.")
        return redirect("request_detail", request_id=request_id)

    FUEL_PRICE_PER_LITER = 100
    DISTANCE_CHARGE_PER_KM = 2
    SERVICE_CHARGE = 50
    max_fuel_liters = 10
    max_distance_km = 50

    if service_request.service_type == "fuel":
        if not service_request.fuel_quantity:
            service_request.fuel_quantity = 5
        if not service_request.distance_km:
            service_request.distance_km = 5
        service_request.final_cost = (
            (service_request.fuel_quantity * FUEL_PRICE_PER_LITER)
            + (service_request.distance_km * DISTANCE_CHARGE_PER_KM)
            + SERVICE_CHARGE
        )
    else:
        base_costs = {
            "mechanic": 800,
            "tire": 400,
            "battery": 600,
            "tow": 1500,
        }
        if not service_request.final_cost:
            service_request.final_cost = base_costs.get(
                service_request.service_type, 500
            )

    service_request.save()

    context = {
        "service_request": service_request,
        "fuel_price_per_liter": FUEL_PRICE_PER_LITER,
        "distance_charge_per_km": DISTANCE_CHARGE_PER_KM,
        "service_charge": SERVICE_CHARGE,
        "max_fuel_liters": max_fuel_liters,
        "max_distance_km": max_distance_km,
    }
    return render(request, "core/payment.html", context)


@login_required
def mark_paid(request, request_id):
    """Process payment with selected method"""
    if request.user.profile.role != "customer":
        messages.error(request, "Only customers can confirm payment.")
        return redirect("dashboard")

    service_request = get_object_or_404(ServiceRequest, request_id=request_id)

    if service_request.user != request.user:
        messages.error(request, "This is not your request.")
        return redirect("dashboard")

    if service_request.status != "completed":
        messages.warning(request, "Service must be completed first.")
        return redirect("request_detail", request_id=request_id)

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")

        if payment_method not in ["card", "upi", "cash"]:
            messages.error(request, "Please select a valid payment method.")
            return redirect("payment_page", request_id=request_id)

        service_request.status = "paid"

        FUEL_PRICE_PER_LITER = 100
        DISTANCE_CHARGE_PER_KM = 2
        SERVICE_CHARGE = 50
        if service_request.service_type == "fuel":
            fuel_quantity = int(request.POST.get("fuel_quantity", 5))
            distance_km = float(request.POST.get("distance_km", 5))
            service_request.fuel_quantity = fuel_quantity
            service_request.distance_km = distance_km
            service_request.final_cost = (
                (fuel_quantity * FUEL_PRICE_PER_LITER)
                + (distance_km * DISTANCE_CHARGE_PER_KM)
                + SERVICE_CHARGE
            )
        elif not service_request.final_cost:
            base_costs = {
                "mechanic": 800,
                "tire": 400,
                "battery": 600,
                "tow": 1500,
            }
            service_request.final_cost = base_costs.get(
                service_request.service_type, 500
            )

        service_request.save()

        ServiceHistory.objects.create(
            service_request=service_request,
            provider=service_request.assigned_provider,
            customer=request.user,
            amount=service_request.final_cost,
            payment_status="paid",
            payment_method=payment_method,
            paid_at=timezone.now(),
        )

        messages.success(
            request,
            f"Payment of ₹{service_request.final_cost} confirmed via {dict(ServiceHistory.PAYMENT_METHOD_CHOICES).get(payment_method)}! Thank you for using our service.",
        )
        return redirect("request_detail", request_id=request_id)

    return redirect("payment_page", request_id=request_id)


@login_required
def view_bill(request, request_id):
    """View bill/receipt after payment"""
    service_request = get_object_or_404(ServiceRequest, request_id=request_id)

    if request.user.profile.role == "customer" and service_request.user != request.user:
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    elif (
        request.user.profile.role == "provider"
        and service_request.assigned_provider != request.user
    ):
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    if service_request.status not in ["paid", "completed"]:
        messages.warning(request, "Bill is only available after payment.")
        return redirect("request_detail", request_id=request_id)

    try:
        history = ServiceHistory.objects.get(service_request=service_request)
    except ServiceHistory.DoesNotExist:
        history = None

    FUEL_PRICE_PER_LITER = 100
    DISTANCE_CHARGE_PER_KM = 2
    SERVICE_CHARGE = 50

    context = {
        "service_request": service_request,
        "history": history,
        "fuel_price_per_liter": FUEL_PRICE_PER_LITER,
        "distance_charge_per_km": DISTANCE_CHARGE_PER_KM,
        "service_charge": SERVICE_CHARGE,
    }
    return render(request, "core/bill.html", context)


@login_required
def upload_service_photo(request, request_id):
    """Customer uploads a photo after service completion"""
    if request.user.profile.role != "customer":
        messages.error(request, "Only customers can upload photos.")
        return redirect("dashboard")

    service_request = get_object_or_404(ServiceRequest, request_id=request_id)

    if service_request.user != request.user:
        messages.error(request, "This is not your request.")
        return redirect("dashboard")

    if service_request.status not in ["completed", "paid"]:
        messages.warning(request, "Service must be completed first.")
        return redirect("request_detail", request_id=request_id)

    if request.method == "POST":
        photo = request.FILES.get("photo")
        if not photo:
            messages.error(request, "Please select a photo to upload.")
            return redirect("request_detail", request_id=request_id)

        try:
            url = upload_file(photo.read(), photo.name)
            # Delete old photo if exists
            if service_request.customer_photo:
                delete_file(service_request.customer_photo)
            service_request.customer_photo = url
            service_request.save()
            messages.success(request, "Photo uploaded successfully!")
        except Exception as e:
            messages.error(request, f"Upload failed: {str(e)}")
        return redirect("request_detail", request_id=request_id)

    context = {"service_request": service_request}
    return render(request, "core/upload_photo.html", context)


@login_required
def rate_service(request, request_id):
    """Customer rates the service after payment"""
    if request.user.profile.role != "customer":
        messages.error(request, "Only customers can rate services.")
        return redirect("dashboard")

    service_request = get_object_or_404(ServiceRequest, request_id=request_id)

    if service_request.user != request.user:
        messages.error(request, "This is not your request.")
        return redirect("dashboard")

    if service_request.status != "paid":
        messages.warning(request, "Service must be paid first.")
        return redirect("request_detail", request_id=request_id)

    if request.method == "POST":
        rating = request.POST.get("rating")
        review = request.POST.get("review", "")

        if not rating or not (1 <= int(rating) <= 5):
            messages.error(request, "Please select a valid rating (1-5 stars).")
            return redirect("request_detail", request_id=request_id)

        try:
            history = ServiceHistory.objects.get(service_request=service_request)
            history.rating = int(rating)
            history.review = review
            history.save()
            messages.success(request, "Thank you for your feedback!")
        except ServiceHistory.DoesNotExist:
            messages.error(request, "Service history not found.")

        return redirect("request_detail", request_id=request_id)

    context = {"service_request": service_request}
    return render(request, "core/rate_service.html", context)


# ==================== Admin Actions ====================


@login_required
def admin_assign_provider(request, request_id):
    """Admin manually assigns a provider to a request"""
    if request.user.profile.role != "admin":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    service_request = get_object_or_404(ServiceRequest, id=request_id)

    if request.method == "POST":
        provider_id = request.POST.get("provider_id")
        if provider_id:
            from django.contrib.auth.models import User

            provider = get_object_or_404(User, id=provider_id)

            if provider.profile.role != "provider":
                messages.error(request, "Selected user is not a provider.")
                return redirect("admin_dashboard")

            service_request.assigned_provider = provider
            service_request.status = "accepted"
            service_request.accepted_at = timezone.now()
            service_request.save()

            messages.success(
                request, f"Provider {provider.get_full_name()} assigned to request."
            )
            return redirect("admin_dashboard")

    providers = UserProfile.objects.filter(role="provider", is_available=True)
    context = {
        "service_request": service_request,
        "providers": providers,
    }
    return render(request, "core/admin_assign_provider.html", context)


@login_required
def admin_toggle_provider_status(request, provider_id):
    """Admin toggles provider availability"""
    if request.user.profile.role != "admin":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    profile = get_object_or_404(UserProfile, user_id=provider_id, role="provider")
    profile.is_available = not profile.is_available
    profile.save()

    status = "available" if profile.is_available else "unavailable"
    messages.success(request, f"Provider {profile.user.username} is now {status}.")
    return redirect("admin_dashboard")


@login_required
def requests_filtered(request, status_filter):
    """Admin view of filtered requests"""
    if request.user.profile.role != "admin":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    valid_filters = [
        "pending",
        "accepted",
        "in_progress",
        "completed",
        "paid",
        "cancelled",
    ]

    if status_filter not in valid_filters:
        status_filter = "pending"

    requests = ServiceRequest.objects.filter(status=status_filter).order_by(
        "-created_at"
    )

    context = {
        "requests": requests,
        "status_filter": status_filter,
        "status_display": dict(ServiceRequest.STATUS_CHOICES).get(
            status_filter, status_filter.title()
        ),
    }
    return render(request, "core/admin_requests_filtered.html", context)


# ==================== Profile Views ====================


@login_required
def profile(request):
    """User profile view"""
    profile = request.user.profile

    if request.method == "POST":
        # Update profile
        profile.phone_number = request.POST.get("phone_number", profile.phone_number)

        if profile.role == "provider":
            profile.vehicle_number = request.POST.get(
                "vehicle_number", profile.vehicle_number
            )
            profile.is_available = request.POST.get("is_available") == "on"
        elif profile.role == "customer":
            profile.default_address = request.POST.get(
                "default_address", profile.default_address
            )

        profile.save()

        # Update user
        request.user.first_name = request.POST.get(
            "first_name", request.user.first_name
        )
        request.user.last_name = request.POST.get("last_name", request.user.last_name)
        request.user.email = request.POST.get("email", request.user.email)
        request.user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    context = {"profile": profile}
    return render(request, "core/profile.html", context)


@login_required
def provider_toggle_availability(request):
    """Provider toggles their availability"""
    if request.user.profile.role != "provider":
        messages.error(request, "Only providers can change availability.")
        return redirect("dashboard")

    profile = request.user.profile
    profile.is_available = not profile.is_available
    profile.save()

    status = "available" if profile.is_available else "unavailable"
    messages.success(request, f"You are now {status} to receive requests.")
    return redirect("provider_dashboard")
