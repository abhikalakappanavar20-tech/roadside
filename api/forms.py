from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, ServiceRequest


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role='customer',
                phone_number=self.cleaned_data['phone_number']
            )
        return user


class ProviderRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    service_type = forms.ChoiceField(choices=UserProfile.SERVICE_TYPE_CHOICES, required=True)
    vehicle_number = forms.CharField(max_length=20, required=False)
    experience_years = forms.IntegerField(min_value=0, required=False, initial=0)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number',
                  'service_type', 'vehicle_number', 'experience_years', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role='provider',
                phone_number=self.cleaned_data['phone_number'],
                service_type=self.cleaned_data['service_type'],
                vehicle_number=self.cleaned_data.get('vehicle_number', ''),
                experience_years=self.cleaned_data.get('experience_years', 0)
            )
        return user


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['service_type', 'issue_description', 'location_lat', 'location_long', 'location_address']
        widgets = {
            'issue_description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe your issue (e.g., "Car won\'t start", "Need 5 liters petrol")'}),
            'location_lat': forms.HiddenInput(),
            'location_long': forms.HiddenInput(),
        }
