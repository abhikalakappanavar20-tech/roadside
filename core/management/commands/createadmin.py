from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import UserProfile


class Command(BaseCommand):
    help = 'Create an admin user for the roadside assist application'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username')
        parser.add_argument('--email', type=str, help='Admin email')
        parser.add_argument('--password', type=str, help='Admin password')

    def handle(self, *args, **options):
        username = options.get('username', 'admin')
        email = options.get('email', 'admin@roadside.com')
        password = options.get('password', 'admin123')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists.'))
            return

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )

        # Create admin profile
        UserProfile.objects.create(
            user=user,
            role='admin',
            phone_number='0000000000'
        )

        self.stdout.write(self.style.SUCCESS(
            f'Admin user created successfully!\n'
            f'Username: {username}\n'
            f'Password: {password}\n'
            f'Please log in and change the password.'
        ))
