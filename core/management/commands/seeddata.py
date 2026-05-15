from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import UserProfile, ServiceRequest
import random


class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create sample customers
        customers_data = [
            {'username': 'customer1', 'first_name': 'John', 'last_name': 'Doe', 'phone': '9876543210'},
            {'username': 'customer2', 'first_name': 'Jane', 'last_name': 'Smith', 'phone': '9876543211'},
            {'username': 'customer3', 'first_name': 'Bob', 'last_name': 'Johnson', 'phone': '9876543212'},
        ]

        for data in customers_data:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    email=f"{data['username']}@example.com",
                    password='password123',
                    first_name=data['first_name'],
                    last_name=data['last_name']
                )
                UserProfile.objects.create(
                    user=user,
                    role='customer',
                    phone_number=data['phone']
                )
                self.stdout.write(f'Created customer: {data["username"]}')

        # Create sample providers
        providers_data = [
            {'username': 'mechanic1', 'first_name': 'Mike', 'last_name': 'Mechanic', 'phone': '9876543220', 'service': 'mechanic', 'vehicle': 'MH01AB1234'},
            {'username': 'fuelguy1', 'first_name': 'Raj', 'last_name': 'Fuel', 'phone': '9876543221', 'service': 'fuel', 'vehicle': 'MH01CD5678'},
            {'username': 'provider3', 'first_name': 'David', 'last_name': 'Both', 'phone': '9876543222', 'service': 'both', 'vehicle': 'MH01EF9012'},
        ]

        for data in providers_data:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    email=f"{data['username']}@example.com",
                    password='password123',
                    first_name=data['first_name'],
                    last_name=data['last_name']
                )
                UserProfile.objects.create(
                    user=user,
                    role='provider',
                    phone_number=data['phone'],
                    service_type=data['service'],
                    vehicle_number=data['vehicle'],
                    is_available=True
                )
                self.stdout.write(f'Created provider: {data["username"]}')

        # Create sample service requests
        service_types = ['fuel', 'mechanic', 'tire', 'battery']
        statuses = ['pending', 'accepted', 'in_progress', 'completed', 'paid']

        customers = User.objects.filter(profile__role='customer')
        providers = User.objects.filter(profile__role='provider')

        for i in range(5):
            customer = random.choice(customers)
            service_type = random.choice(service_types)
            status = random.choice(statuses)

            request = ServiceRequest.objects.create(
                user=customer,
                service_type=service_type,
                status=status,
                location_lat=19.0760 + random.uniform(-0.1, 0.1),
                location_long=72.8777 + random.uniform(-0.1, 0.1),
                location_address=f'Sample Location {i+1}, Mumbai',
                issue_description=f'Sample {service_type} request {i+1}'
            )

            if status in ['accepted', 'in_progress', 'completed', 'paid'] and providers.exists():
                request.assigned_provider = random.choice(providers)
                if status == 'paid':
                    request.final_cost = random.choice([400, 500, 600, 800, 1500])
                request.save()

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write('\nLogin credentials (all passwords: password123):')
        self.stdout.write('Customers: customer1, customer2, customer3')
        self.stdout.write('Providers: mechanic1, fuelguy1, provider3')
