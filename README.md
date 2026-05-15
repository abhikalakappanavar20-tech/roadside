# Roadside Assistance MVP

A Django-based Uber-like web application for on-road breakdown and fuel assistance services. This three-sided marketplace connects customers needing emergency roadside help with service providers, managed by platform administrators.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [User Roles & Features](#user-roles--features)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Database Models](#database-models)
6. [How It Works](#how-it-works)
7. [API Endpoints](#api-endpoints)
8. [Service Pricing](#service-pricing)
9. [Installation & Setup](#installation--setup)
10. [External Q&A](#external-qa)
11. [Browser Support](#browser-support)
12. [Future Enhancements](#future-enhancements)
13. [Troubleshooting](#troubleshooting)
14. [License](#license)

---

## Project Overview

This is a **three-sided marketplace platform** for roadside assistance:

| Role | Description |
|------|-------------|
| **Customers** | Request emergency services (fuel delivery, mechanic, tire repair, battery jumpstart, towing) |
| **Service Providers** | Accept and fulfill service requests from customers |
| **Admins** | Manage the platform, assign providers, and monitor all activities |

### Key Features
- Real-time request tracking with auto-refresh
- GPS location detection via browser geolocation
- Interactive maps using Leaflet.js + OpenStreetMap (free, no API key)
- Simulated payment system (Card/UPI/Cash)
- Rating and review system
- Google Maps navigation for providers
- Live dashboard with earnings tracking
- Admin panel with statistics and management tools

---

## User Roles & Features

### Customers
- Register/login with customer role
- Request services: fuel delivery, mechanic, tire repair, battery jumpstart, or towing
- Automatic GPS location detection via browser geolocation
- Interactive map to verify/correct location
- Real-time status tracking: `pending → accepted → in_progress → completed → paid`
- View assigned provider details and contact information
- Make simulated payments (Card/UPI/Cash)
- Upload photos of the issue
- Rate and review completed services
- View service history and bills

### Service Providers
- Register with service specialty (Fuel Delivery, Mechanic/Breakdown, or Both)
- Live auto-refreshing dashboard showing nearby pending requests
- Availability toggle (go online/offline)
- Accept pending requests matching their service type
- One-click Google Maps navigation to customer location
- Update request status: start service, complete service
- Track earnings and service history
- View average rating from customers

### Admins
- Protected admin dashboard with overview statistics
- View all service requests, providers, and customers
- Manual provider-to-request assignment
- Filter requests by status (pending, accepted, in_progress, completed, paid, cancelled)
- Toggle provider availability
- Monitor platform activity in real-time

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Django 6.0.2 | Web framework |
| **Database** | SQLite | Development database |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript | User interface |
| **CSS Framework** | Bootstrap 5 | Responsive styling |
| **Maps** | Leaflet.js + OpenStreetMap | Free mapping (no API key required) |
| **Icons** | Bootstrap Icons | UI icons |
| **Image Handling** | Pillow | Photo uploads |

---

## Project Structure

```
Project15/
├── api/                              # Data models and API layer
│   ├── models.py                     # UserProfile, ServiceRequest, ServiceHistory, ProviderLocation
│   ├── serializers.py                # API endpoints (JSON responses)
│   ├── forms.py                      # Registration forms
│   ├── admin.py                      # Django admin configuration
│   ├── urls.py                       # API URL routes
│   └── migrations/                   # Database migrations
│
├── core/                             # Views, templates, and middleware
│   ├── views.py                      # All view functions (755 lines)
│   ├── urls.py                       # URL routing for web pages
│   ├── middleware.py                 # Authentication middleware (NoCache)
│   ├── models.py                     # Empty (uses api models)
│   └── templates/core/              # HTML templates (20 files)
│       ├── base.html                 # Base template with nav
│       ├── home.html                 # Landing page
│       ├── customer_dashboard.html   # Customer dashboard
│       ├── provider_dashboard.html   # Provider dashboard
│       ├── admin_dashboard.html      # Admin dashboard
│       ├── new_request.html          # Create service request
│       ├── request_detail.html       # Track request status
│       ├── payment.html              # Payment page
│       ├── bill.html                 # Bill/receipt view
│       ├── rate_service.html         # Rating page
│       ├── profile.html              # User profile
│       ├── upload_photo.html         # Photo upload
│       ├── customer_login.html       # Customer login
│       ├── customer_register.html    # Customer registration
│       ├── provider_login.html       # Provider login
│       ├── provider_register.html    # Provider registration
│       ├── admin_assign_provider.html # Admin assign provider
│       └── admin_requests_filtered.html # Filtered requests view
│
├── roadside_assist/                  # Django project configuration
│   ├── settings.py                   # Project settings
│   ├── urls.py                       # Main URL routing
│   ├── wsgi.py                       # WSGI config
│   └── asgi.py                       # ASGI config
│
├── static/                           # Static files
│   ├── css/style.css                 # Custom styles
│   └── js/main.js                    # JavaScript functions
│
├── media/                            # User uploads
│   └── service_photos/               # Customer uploaded photos
│
├── manage.py                         # Django management script
├── requirements.txt                  # Python dependencies
├── db.sqlite3                        # SQLite database
├── README.md                         # This file
└── start_cloudflare.py               # Cloudflare tunnel script
```

---

## Database Models

### 1. UserProfile (Extends Django User Model)

Stores role-based data for all users.

| Field | Type | Description |
|-------|------|-------------|
| `user` | OneToOneField | Links to Django User model |
| `role` | CharField | customer, provider, or admin |
| `phone_number` | CharField | Contact number |
| `service_type` | CharField | fuel, mechanic, or both (providers only) |
| `is_available` | BooleanField | Online/offline status (providers) |
| `latitude/longitude` | DecimalField | GPS coordinates |
| `vehicle_number` | CharField | Provider's vehicle number |
| `experience_years` | IntegerField | Years of experience (providers) |
| `default_address` | TextField | Customer's saved address |

**Properties:**
- `can_provide_fuel` - Returns True if service_type is "fuel" or "both"
- `can_provide_mechanic` - Returns True if service_type is "mechanic" or "both"
- `average_rating` - Calculates average rating from ServiceHistory
- `rating_count` - Returns count of ratings received

### 2. ServiceRequest (Main Request Entity)

Tracks all service requests from creation to payment.

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | CharField | Auto-generated unique ID (e.g., SR20260426001) |
| `user` | ForeignKey | Customer who created the request |
| `service_type` | CharField | fuel, mechanic, tire, battery, or tow |
| `status` | CharField | pending → accepted → in_progress → completed → paid → cancelled |
| `location_lat/long` | DecimalField | GPS coordinates |
| `location_address` | TextField | Street address (optional) |
| `assigned_provider` | ForeignKey | Provider handling the request |
| `issue_description` | TextField | Customer's description of the issue |
| `fuel_quantity` | IntegerField | Liters of fuel (for fuel services) |
| `distance_km` | DecimalField | Distance for fuel delivery |
| `estimated_cost` | DecimalField | Initial cost estimate |
| `final_cost` | DecimalField | Final cost after service |
| `customer_photo` | ImageField | Photo uploaded by customer |
| `created_at` | DateTimeField | When request was created |
| `accepted_at` | DateTimeField | When provider accepted |
| `started_at` | DateTimeField | When service started |
| `completed_at` | DateTimeField | When service completed |

**Properties:**
- `is_active` - Returns True if status is pending, accepted, or in_progress
- `customer_name` - Returns customer's full name or username
- `customer_phone` - Returns customer's phone number

### 3. ServiceHistory (Completed Services)

Tracks completed services and payment details.

| Field | Type | Description |
|-------|------|-------------|
| `service_request` | OneToOneField | Links to original ServiceRequest |
| `provider` | ForeignKey | Service provider |
| `customer` | ForeignKey | Customer |
| `service_notes` | TextField | Provider's completion notes |
| `completion_photo` | URLField | Photo URL of completed service |
| `amount` | DecimalField | Payment amount |
| `payment_status` | CharField | pending, paid, or refunded |
| `payment_method` | CharField | card, upi, or cash |
| `paid_at` | DateTimeField | When payment was made |
| `rating` | IntegerField | 1-5 star rating |
| `review` | TextField | Text review from customer |

### 4. ProviderLocation (Real-Time Tracking)

Stores provider location history for navigation.

| Field | Type | Description |
|-------|------|-------------|
| `provider` | ForeignKey | Provider user |
| `latitude/longitude` | DecimalField | Current location |
| `timestamp` | DateTimeField | When location was recorded |

---

## How It Works

### Complete Request Lifecycle

```
Customer                          Provider                        Admin
   |                                   |                              |
   |-- Create Request --> pending ---->|                              |
   |                                   |-- Accept Request --> accepted|
   |                                   |                              |
   |<-- View Provider Details ---------|                              |
   |                                   |-- Start Service --> in_progress
   |                                   |                              |
   |                                   |-- Complete Service --> completed
   |                                   |                              |
   |-- View Bill/Pay --> paid -------->|                              |
   |                                   |                              |
   |-- Rate & Review --> history ------|                              |
   |                                   |                              |
   |                                   |<-- Monitor (dashboard) ------|
```

### Step-by-Step Flows

#### Customer Flow
1. Register as customer at `/customer/register/`
2. Login at `/customer/login/`
3. Click "New Request" on dashboard
4. Grant browser location permission (GPS detection)
5. Verify/correct location on interactive map
6. Select service type (fuel, mechanic, tire, battery, tow)
7. Add issue description and submit
8. Dashboard auto-refreshes to show request status
9. When provider accepts, view provider details (name, phone, vehicle)
10. Track progress: accepted → in_progress → completed
11. Receive notification when service is completed
12. Make payment: choose Card/UPI/Cash and confirm
13. View bill/receipt
14. Rate and review the service (1-5 stars + text)

#### Provider Flow
1. Register as provider at `/provider/register/`
2. Select service specialty: Fuel Delivery, Mechanic, or Both
3. Login at `/provider/login/` (automatically set to available)
4. Dashboard shows live feed of pending requests (auto-refreshes every 30s)
5. Filter requests by service type (matching your specialty)
6. Click "Accept" on a suitable request
7. Use "Navigate" button to open Google Maps with customer location
8. Click "Start Service" when you arrive at location
9. Complete the service and click "Complete Service"
10. Customer confirms payment
11. View updated earnings on dashboard
12. Check service history and average rating

#### Admin Flow
1. Create superuser: `python manage.py createsuperuser`
2. Login at `/admin/` or `/admin/dashboard/`
3. View platform statistics:
   - Total requests
   - Pending/Active/Completed requests
   - Total providers (available/unavailable)
   - Total customers
4. Filter requests by status: `/admin/requests/<status>/`
5. Manually assign providers to pending requests if needed
6. Toggle provider availability: `/admin/toggle-provider/<id>/`
7. Monitor all platform activity in real-time

---

## API Endpoints

### Authentication
All API endpoints require authentication. Include session cookies or use Django's auth system.

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/pending-requests/` | GET | Get pending requests (providers only) | JSON: `{requests: [...]}` |
| `/api/accept/<id>/` | POST | Accept a pending request (providers) | JSON: `{success, request_id}` |
| `/api/my-requests/` | GET | Provider's active requests | JSON: `{requests: [...]}` |
| `/api/customer-requests/` | GET | Customer's all requests | JSON: `{requests: [...]}` |
| `/api/update-status/<id>/` | POST | Update request status | JSON: `{success, status}` |
| `/api/update-location/` | POST | Update provider GPS location | JSON: `{success: true}` |
| `/api/create-request/` | POST | Create new service request | JSON: `{success, request_id}` |
| `/api/stats/` | GET | Admin dashboard statistics | JSON: `{total_requests, pending, ...}` |

### API Request/Response Examples

**Get Pending Requests** (Provider)
```bash
GET /api/pending-requests/
Response: {
  "requests": [
    {
      "id": 1,
      "request_id": "SR20260428001",
      "service_type": "Fuel Delivery",
      "service_type_code": "fuel",
      "status": "pending",
      "location_lat": 28.6139,
      "location_long": 77.2090,
      "location_address": "123 Main St",
      "issue_description": "Out of fuel",
      "customer_name": "John Doe",
      "customer_phone": "+1234567890",
      "created_at": "2026-04-28T10:30:00Z",
      "time_ago": "5 mins ago"
    }
  ]
}
```

**Update Provider Location**
```bash
POST /api/update-location/
Body: {"latitude": 28.6139, "longitude": 77.2090}
Response: {"success": true}
```

**Get Admin Stats**
```bash
GET /api/stats/
Response: {
  "total_requests": 150,
  "pending": 12,
  "accepted": 5,
  "in_progress": 3,
  "completed": 20,
  "paid": 110,
  "total_providers": 25,
  "active_providers": 18,
  "total_customers": 200
}
```

---

## Service Pricing

### Cost Calculation

| Service Type | Base Cost | Pricing Details |
|--------------|-----------|-----------------|
| **Fuel Delivery** | ₹500 base | ₹100/liter + ₹2/km distance + ₹50 service charge |
| **Mechanic** | ₹800 | Fixed rate |
| **Tire Puncture** | ₹400 | Fixed rate |
| **Battery Jumpstart** | ₹600 | Fixed rate |
| **Towing** | ₹1,500 | Fixed rate |

### Fuel Service Cost Formula
```
final_cost = (fuel_quantity × 100) + (distance_km × 2) + 50
```

Example: 5 liters fuel delivered 10km away = (5×100) + (10×2) + 50 = ₹570

### Customizing Prices
Edit cost constants in `core/views.py`:
- `payment_page()` function (line ~397)
- `mark_paid()` function (line ~464)

```python
FUEL_PRICE_PER_LITER = 100  # Change this
DISTANCE_CHARGE_PER_KM = 2   # Change this
SERVICE_CHARGE = 50           # Change this

base_costs = {
    "mechanic": 800,          # Change this
    "tire": 400,               # Change this
    "battery": 600,            # Change this
    "tow": 1500,               # Change this
}
```

---

## Installation & Setup

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Git (optional, for version control)

### Quick Start

1. **Clone or navigate to project directory**
   ```bash
   cd C:/Project15
   ```

2. **Install dependencies**
   ```bash
   pip install django==6.0.2 Pillow
   ```
   Or use requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create admin superuser**
   ```bash
   python manage.py createsuperuser
   ```
   Follow prompts for username, email, and password.

5. **Run development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Django Admin: http://127.0.0.1:8000/admin/

### User Registration URLs
- Customer Registration: http://127.0.0.1:8000/customer/register/
- Provider Registration: http://127.0.0.1:8000/provider/register/

### Making a User Admin
1. Login to Django Admin: `/admin/`
2. Go to Users section
3. Select the user
4. In their Profile, change role to "Admin"
5. Save changes

### Running with Cloudflare Tunnel (Optional)
For remote access/testing:
```bash
python start_cloudflare.py
```
This creates a public URL accessible from anywhere.

---

## External Q&A

**Q: What is this project about?**
A: It's a roadside assistance marketplace platform that connects customers with vehicle breakdown emergencies to service providers who can deliver fuel, fix tires, jump-start batteries, provide mechanical repairs, or tow vehicles. Think "Uber for roadside assistance."

**Q: How do customers request help?**
A: Customers register, click "New Request" on their dashboard, grant location access (or manually enter location on map), select the service type needed (fuel, mechanic, tire, battery, tow), add a description, and submit. They can then track the request status in real-time with auto-refreshing dashboard.

**Q: How do providers get work?**
A: Providers register with their specialty (Fuel Delivery and/or Mechanic). When they're online (available), they see a live auto-refreshing feed of nearby pending requests matching their service type. They can review request details (location, issue description) and accept any request they want to fulfill.

**Q: How does the payment system work?**
A: This is currently a demo/simulation with no real money processing. When a service is completed, customers go to a payment page where they can choose from three simulated payment methods: Credit/Debit Card, UPI, or Cash on Service. They confirm the payment, which updates the request status to "paid" and creates a ServiceHistory record.

**Q: Is this ready for production?**
A: No, this is an MVP (Minimum Viable Product) intended for demonstration, educational, or prototype purposes. For production use, you would need:
- Real payment gateway integration (Razorpay, Stripe, PayPal)
- Push notifications (Firebase, WebSocket)
- In-app chat/messaging system
- SSL/HTTPS encryption
- Production database (PostgreSQL, MySQL)
- Proper error handling and logging
- Email/SMS notifications
- User verification system
- Terms of service and privacy policy

**Q: What technologies does it use?**
A: The stack is Django 6.0.2 (Python web framework) with SQLite database, Bootstrap 5 for responsive frontend, Leaflet.js with OpenStreetMap for free mapping (no paid API keys), and Vanilla JavaScript for interactivity. The project uses Pillow for image handling.

**Q: Can I customize the services or pricing?**
A: Yes, easily! To modify service types, edit the `SERVICE_TYPE_CHOICES` in `api/models.py` (ServiceRequest model). To change pricing, edit the cost constants in `core/views.py` in the `payment_page()` and `mark_paid()` functions. You can also add new service types, modify the base costs, or implement dynamic pricing.

**Q: How does the real-time auto-refresh work?**
A: The provider and customer dashboards use JavaScript `setInterval()` to make AJAX calls to the API endpoints every 30 seconds. The API returns updated request data in JSON format, and the frontend dynamically updates the UI without requiring a page refresh.

**Q: Is the map feature free to use?**
A: Yes, the project uses Leaflet.js with OpenStreetMap tiles, which are completely free and require no API keys or registration. This makes it easy to run without any setup or costs.

**Q: Can providers see customer locations on a map?**
A: Yes, when a provider accepts a request, they can click the "Navigate" button which opens Google Maps with the customer's GPS coordinates pre-filled. This allows for easy navigation to the customer's location.

**Q: How are ratings calculated?**
A: After a service is paid, customers can rate it 1-5 stars and leave a text review. The `UserProfile` model has an `average_rating` property that calculates the average of all ratings received by a provider from the ServiceHistory table.

---

## Browser Support

| Browser | Status | Notes |
|---------|--------|-------|
| Chrome/Edge | ✅ Full Support | Recommended |
| Firefox | ✅ Full Support | Works well |
| Safari | ✅ Full Support | May need to enable location services |
| Mobile Browsers | ✅ Responsive | Bootstrap 5 responsive design |

**Important Notes:**
- Geolocation requires HTTPS in production. On localhost, it works with HTTP.
- For production deployment, configure SSL/HTTPS to enable location services.
- Maps require an active internet connection to load tiles.

---

## Future Enhancements

### Phase 1: Core Features
- [ ] Real payment gateway integration (Razorpay, Stripe)
- [ ] Push notifications (Web Push API / Firebase)
- [ ] In-app chat between customer and provider
- [ ] Email and SMS notifications
- [ ] Provider verification system (documents, background check)

### Phase 2: User Experience
- [ ] Provider ratings displayed to customers before accepting
- [ ] Advanced analytics dashboard with charts
- [ ] Multi-language support (i18n)
- [ ] Dark mode toggle
- [ ] Mobile app (React Native / Flutter)

### Phase 3: Business Features
- [ ] Subscription plans for providers
- [ ] Surge pricing during peak hours
- [ ] Service scheduling (book for later)
- [ ] Multiple stops for towing
- [ ] Emergency contact integration (auto-call)

### Phase 4: Advanced
- [ ] AI-powered request routing
- [ ] Dynamic pricing based on demand
- [ ] Provider leaderboard and incentives
- [ ] Customer loyalty program
- [ ] Corporate accounts

---

## Troubleshooting

### Location Not Detected
**Problem:** GPS location is not being detected.
**Solutions:**
- Grant browser location permission (check address bar icon)
- Try a different browser (Chrome/Edge recommended)
- Enable GPS on mobile devices
- Manually enter address and click on map to set location
- Check if you're on HTTPS (required for production)

### Maps Not Loading
**Problem:** Leaflet map is blank or not displaying.
**Solutions:**
- Check internet connection (OpenStreetMap requires internet)
- Check browser console (F12) for JavaScript errors
- Clear browser cache and reload
- Disable ad blockers temporarily

### Auto-Refresh Not Working
**Problem:** Dashboard not updating automatically.
**Solutions:**
- Check browser console for JavaScript errors
- Ensure you're logged in (API requires authentication)
- Check if CSRF token is properly set
- Try refreshing the page manually

### Database Errors
**Problem:** Migration errors or database locked.
**Solutions:**
```bash
# Reset database (WARNING: deletes all data)
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Can't Access Admin
**Problem:** Getting "Access Denied" on admin pages.
**Solutions:**
- Ensure you created a superuser: `python manage.py createsuperuser`
- Login at `/admin/` first
- Update user role to "admin" in Django Admin: `/admin/` → Users → Select user → Change Profile role to "Admin"
- Check that your user has `is_staff` and `is_superuser` flags set

### Static Files Not Loading
**Problem:** CSS/JS not loading properly.
**Solutions:**
```bash
# Collect static files
python manage.py collectstatic

# Check settings
# Ensure STATIC_URL and STATIC_ROOT are correctly set in settings.py
```

### Photo Upload Fails
**Problem:** Cannot upload customer photos.
**Solutions:**
- Ensure `media/` directory exists and is writable
- Check that Pillow is installed: `pip install Pillow`
- Verify `MEDIA_URL` and `MEDIA_ROOT` in settings.py
- Check file size (may be too large for server)

---

## License

This is an educational/demo project released under the MIT License. Feel free to use and modify for learning, prototyping, or as a starting point for your own projects.

**Attribution appreciated but not required.**

---

## Contact & Support

For questions, issues, or contributions:
- Review this README thoroughly
- Check the code comments in `core/views.py` and `api/models.py`
- Examine the Django debug pages when running in DEBUG mode
- Test the API endpoints directly to understand data flow

**Built with Django 6.0.2 | Last Updated: April 2026**
