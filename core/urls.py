from django.urls import path
from . import views

urlpatterns = [
    # Home & Auth
    path("", views.home, name="home"),
    path("customer/register/", views.customer_register, name="customer_register"),
    path("provider/register/", views.provider_register, name="provider_register"),
    path("customer/login/", views.customer_login, name="customer_login"),
    path("provider/login/", views.provider_login, name="provider_login"),
    path("logout/", views.logout_view, name="logout"),
    # Dashboards
    path("dashboard/", views.dashboard, name="dashboard"),
    path("customer/dashboard/", views.customer_dashboard, name="customer_dashboard"),
    path("provider/dashboard/", views.provider_dashboard, name="provider_dashboard"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    # Service Requests
    path("request/new/", views.new_request, name="new_request"),
    path("request/<str:request_id>/", views.request_detail, name="request_detail"),
    # Provider Actions
    path(
        "provider/accept/<int:request_id>/", views.accept_request, name="accept_request"
    ),
    path("provider/start/<str:request_id>/", views.start_service, name="start_service"),
    path(
        "provider/complete/<str:request_id>/",
        views.complete_service,
        name="complete_service",
    ),
    path(
        "provider/toggle-availability/",
        views.provider_toggle_availability,
        name="toggle_availability",
    ),
    # Customer Actions
    path("customer/pay/<str:request_id>/", views.payment_page, name="payment_page"),
    path("customer/pay/process/<str:request_id>/", views.mark_paid, name="mark_paid"),
    path("customer/bill/<str:request_id>/", views.view_bill, name="view_bill"),
    path("customer/bill/<str:request_id>/download/", views.download_bill_pdf, name="download_bill"),
    path("customer/rate/<str:request_id>/", views.rate_service, name="rate_service"),
    path(
        "customer/upload-photo/<str:request_id>/",
        views.upload_service_photo,
        name="upload_photo",
    ),
    # Admin Actions
    path(
        "admin/assign/<int:request_id>/",
        views.admin_assign_provider,
        name="admin_assign_provider",
    ),
    path(
        "admin/toggle-provider/<int:provider_id>/",
        views.admin_toggle_provider_status,
        name="admin_toggle_provider",
    ),
    path(
        "admin/requests/<str:status_filter>/",
        views.requests_filtered,
        name="requests_filtered",
    ),
    # Profile
    path("profile/", views.profile, name="profile"),
]
