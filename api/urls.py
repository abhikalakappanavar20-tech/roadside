from django.urls import path
from . import serializers

urlpatterns = [
    # API endpoints
    path('pending-requests/', serializers.get_pending_requests, name='api_pending_requests'),
    path('accept/<int:request_id>/', serializers.accept_request, name='api_accept_request'),
    path('my-requests/', serializers.get_my_requests, name='api_my_requests'),
    path('customer-requests/', serializers.get_customer_requests, name='api_customer_requests'),
    path('update-status/<int:request_id>/', serializers.update_request_status, name='api_update_status'),
    path('update-location/', serializers.update_provider_location, name='api_update_location'),
    path('create-request/', serializers.create_service_request, name='api_create_request'),
    path('stats/', serializers.get_all_requests_stats, name='api_stats'),
]
