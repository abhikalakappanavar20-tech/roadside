from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with role and additional fields"""

    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("provider", "Provider"),
        ("admin", "Admin"),
    ]

    SERVICE_TYPE_CHOICES = [
        ("fuel", "Fuel Delivery"),
        ("mechanic", "Mechanic/Breakdown"),
        ("both", "Both Services"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # Provider specific fields
    service_type = models.CharField(
        max_length=20, choices=SERVICE_TYPE_CHOICES, blank=True, null=True
    )
    is_available = models.BooleanField(default=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    experience_years = models.IntegerField(default=0)

    # Customer specific fields
    default_address = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    @property
    def can_provide_fuel(self):
        return self.service_type in ["fuel", "both"]

    @property
    def can_provide_mechanic(self):
        return self.service_type in ["mechanic", "both"]

    @property
    def average_rating(self):
        ratings = ServiceHistory.objects.filter(
            provider=self.user, rating__isnull=False
        ).values_list("rating", flat=True)
        if ratings:
            return round(sum(ratings) / len(ratings), 1)
        return 0

    @property
    def rating_count(self):
        return ServiceHistory.objects.filter(
            provider=self.user, rating__isnull=False
        ).count()


class ServiceRequest(models.Model):
    """Main service request model for customer breakdown/fuel requests"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    SERVICE_TYPE_CHOICES = [
        ("fuel", "Fuel Delivery"),
        ("mechanic", "Mechanic/Breakdown"),
        ("tire", "Tire Puncture"),
        ("battery", "Battery Jumpstart"),
        ("tow", "Towing Service"),
    ]

    # Request identifiers
    request_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="service_requests"
    )

    # Service details
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    issue_description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Location details
    location_lat = models.DecimalField(max_digits=9, decimal_places=6)
    location_long = models.DecimalField(max_digits=9, decimal_places=6)
    location_address = models.TextField(blank=True, null=True)

    # Provider assignment
    assigned_provider = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_requests",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Payment
    fuel_quantity = models.IntegerField(
        null=True, blank=True, help_text="Liters of fuel for fuel services"
    )
    distance_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Distance in km for fuel delivery",
    )
    estimated_cost = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    final_cost = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    # Customer uploaded photos (stores Vercel Blob URL)
    customer_photo = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.request_id} - {self.service_type} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.request_id:
            from django.utils import timezone
            import random
            import string

            timestamp = timezone.now().strftime("%Y%m%d")
            random_str = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=4)
            )
            self.request_id = f"SR{timestamp}{random_str}"
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status in ["pending", "accepted", "in_progress"]

    @property
    def customer_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def customer_phone(self):
        return self.user.profile.phone_number


class ServiceHistory(models.Model):
    """Track completed service history and payments"""

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("refunded", "Refunded"),
    ]

    service_request = models.OneToOneField(
        ServiceRequest, on_delete=models.CASCADE, related_name="history"
    )
    provider = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="service_histories"
    )
    customer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="customer_histories"
    )

    # Service completion details
    service_notes = models.TextField(blank=True, null=True)
    completion_photo = models.URLField(blank=True, null=True)

    PAYMENT_METHOD_CHOICES = [
        ("card", "Credit/Debit Card"),
        ("upi", "UPI"),
        ("cash", "Cash on Service"),
    ]

    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True
    )
    paid_at = models.DateTimeField(null=True, blank=True)

    # Rating
    rating = models.IntegerField(null=True, blank=True)
    review = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"History {self.service_request.request_id} - {self.payment_status}"


class ProviderLocation(models.Model):
    """Track provider real-time location for navigation"""

    provider = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="locations"
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        get_latest_by = "timestamp"

    def __str__(self):
        return f"{self.provider.username} at {self.latitude}, {self.longitude}"
