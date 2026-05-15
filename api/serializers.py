from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json

from .models import ServiceRequest, UserProfile, ProviderLocation


def get_pending_requests(request):
    """API endpoint for providers to get pending service requests"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        profile = request.user.profile
        if profile.role != 'provider' or not profile.is_available:
            return JsonResponse({'requests': []})

        # Get service types this provider can handle
        can_provide = []
        if profile.can_provide_fuel:
            can_provide.append('fuel')
        if profile.can_provide_mechanic:
            can_provide.extend(['mechanic', 'tire', 'battery', 'tow'])

        # Get pending requests that match provider's service type
        pending_requests = ServiceRequest.objects.filter(
            status='pending',
            service_type__in=can_provide
        ).order_by('-created_at')[:20]

        requests_data = []
        for req in pending_requests:
            requests_data.append({
                'id': req.id,
                'request_id': req.request_id,
                'service_type': req.get_service_type_display(),
                'service_type_code': req.service_type,
                'status': req.status,
                'location_lat': float(req.location_lat),
                'location_long': float(req.location_long),
                'location_address': req.location_address,
                'issue_description': req.issue_description,
                'customer_name': req.customer_name,
                'customer_phone': req.customer_phone,
                'created_at': req.created_at.isoformat(),
                'time_ago': get_time_ago(req.created_at),
            })

        return JsonResponse({'requests': requests_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def accept_request(request, request_id):
    """API endpoint for providers to accept a service request"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        profile = request.user.profile
        if profile.role != 'provider':
            return JsonResponse({'error': 'Only providers can accept requests'}, status=403)

        service_request = ServiceRequest.objects.get(id=request_id)

        # Check if request is still pending
        if service_request.status != 'pending':
            return JsonResponse({'error': 'Request is no longer available'}, status=400)

        # Check if provider can handle this service type
        if service_request.service_type == 'fuel' and not profile.can_provide_fuel:
            return JsonResponse({'error': 'You are not authorized to provide fuel services'}, status=403)
        if service_request.service_type != 'fuel' and not profile.can_provide_mechanic:
            return JsonResponse({'error': 'You are not authorized to provide mechanic services'}, status=403)

        # Update request
        service_request.status = 'accepted'
        service_request.assigned_provider = request.user
        service_request.accepted_at = timezone.now()
        service_request.save()

        return JsonResponse({
            'success': True,
            'request_id': service_request.request_id,
            'message': 'Request accepted successfully'
        })

    except ServiceRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_my_requests(request):
    """API endpoint for providers to get their accepted/in-progress requests"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        profile = request.user.profile
        if profile.role != 'provider':
            return JsonResponse({'error': 'Only providers can access this'}, status=403)

        # Get requests assigned to this provider
        my_requests = ServiceRequest.objects.filter(
            assigned_provider=request.user,
            status__in=['accepted', 'in_progress']
        ).order_by('-created_at')

        requests_data = []
        for req in my_requests:
            requests_data.append({
                'id': req.id,
                'request_id': req.request_id,
                'service_type': req.get_service_type_display(),
                'status': req.status,
                'location_lat': float(req.location_lat),
                'location_long': float(req.location_long),
                'location_address': req.location_address,
                'issue_description': req.issue_description,
                'customer_name': req.customer_name,
                'customer_phone': req.customer_phone,
                'created_at': req.created_at.isoformat(),
                'accepted_at': req.accepted_at.isoformat() if req.accepted_at else None,
            })

        return JsonResponse({'requests': requests_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def update_request_status(request, request_id):
    """API endpoint to update request status"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)
        new_status = data.get('status')

        if not new_status:
            return JsonResponse({'error': 'Status is required'}, status=400)

        service_request = ServiceRequest.objects.get(id=request_id)

        # Check permissions
        if request.user.profile.role == 'provider':
            if service_request.assigned_provider != request.user:
                return JsonResponse({'error': 'Not your request'}, status=403)
        elif request.user.profile.role == 'customer':
            if service_request.user != request.user:
                return JsonResponse({'error': 'Not your request'}, status=403)
        elif request.user.profile.role != 'admin':
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Update status and timestamps
        service_request.status = new_status
        if new_status == 'in_progress':
            service_request.started_at = timezone.now()
        elif new_status == 'completed':
            service_request.completed_at = timezone.now()

        service_request.save()

        return JsonResponse({
            'success': True,
            'status': service_request.status
        })

    except ServiceRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_customer_requests(request):
    """API endpoint for customers to get their requests"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        requests_qs = ServiceRequest.objects.filter(
            user=request.user
        ).order_by('-created_at')

        requests_data = []
        for req in requests_qs:
            provider_info = None
            if req.assigned_provider:
                try:
                    provider_profile = req.assigned_provider.profile
                    provider_info = {
                        'name': req.assigned_provider.get_full_name() or req.assigned_provider.username,
                        'phone': provider_profile.phone_number,
                        'vehicle_number': provider_profile.vehicle_number,
                    }
                except Exception:
                    provider_info = {
                        'name': req.assigned_provider.get_full_name() or req.assigned_provider.username,
                    }

            requests_data.append({
                'id': req.id,
                'request_id': req.request_id,
                'service_type': req.get_service_type_display(),
                'status': req.status,
                'location_address': req.location_address,
                'issue_description': req.issue_description,
                'assigned_provider': provider_info,
                'estimated_cost': str(req.estimated_cost) if req.estimated_cost else None,
                'final_cost': str(req.final_cost) if req.final_cost else None,
                'created_at': req.created_at.isoformat(),
                'time_ago': get_time_ago(req.created_at),
            })

        return JsonResponse({'requests': requests_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def update_provider_location(request):
    """API endpoint for providers to update their location"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)
        lat = data.get('latitude')
        lng = data.get('longitude')

        if not lat or not lng:
            return JsonResponse({'error': 'Latitude and longitude required'}, status=400)

        profile = request.user.profile
        profile.latitude = lat
        profile.longitude = lng
        profile.save()

        ProviderLocation.objects.create(
            provider=request.user,
            latitude=lat,
            longitude=lng
        )

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def create_service_request(request):
    """API endpoint to create a new service request"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)

        service_type = data.get('service_type')
        lat = data.get('latitude')
        lng = data.get('longitude')
        address = data.get('address')
        description = data.get('description', '')

        if not all([service_type, lat, lng]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        service_request = ServiceRequest.objects.create(
            user=request.user,
            service_type=service_type,
            location_lat=lat,
            location_long=lng,
            location_address=address,
            issue_description=description,
            status='pending'
        )

        return JsonResponse({
            'success': True,
            'request_id': service_request.request_id,
            'id': service_request.id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_time_ago(dt):
    """Helper to get time ago string"""
    from django.utils import timezone
    delta = timezone.now() - dt
    seconds = delta.total_seconds()

    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f'{mins} min ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours > 1 else ""} ago'
    else:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days > 1 else ""} ago'


def get_all_requests_stats(request):
    """API endpoint for admin dashboard stats"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.user.profile.role != 'admin':
        return JsonResponse({'error': 'Admin access required'}, status=403)

    try:
        stats = {
            'total_requests': ServiceRequest.objects.count(),
            'pending': ServiceRequest.objects.filter(status='pending').count(),
            'accepted': ServiceRequest.objects.filter(status='accepted').count(),
            'in_progress': ServiceRequest.objects.filter(status='in_progress').count(),
            'completed': ServiceRequest.objects.filter(status='completed').count(),
            'paid': ServiceRequest.objects.filter(status='paid').count(),
            'total_providers': UserProfile.objects.filter(role='provider').count(),
            'active_providers': UserProfile.objects.filter(role='provider', is_available=True).count(),
            'total_customers': UserProfile.objects.filter(role='customer').count(),
        }

        return JsonResponse(stats)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
