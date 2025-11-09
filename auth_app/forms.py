from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.core.validators import ValidationError
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users with email or phone"""
    
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'first_name', )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        phone_number = cleaned_data.get('phone_number')
        
        if not email and not phone_number:
            raise ValidationError('Either email or phone number must be provided.')
        
        return cleaned_data


class CustomUserChangeForm(UserChangeForm):
    """Form for updating users"""
    
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'first_name', 'last_name', 
                 'timezone', 'email_notifications', 'push_notifications')


class EmailOrPhoneAuthenticationForm(AuthenticationForm):
    """Custom authentication form using email or phone number"""
    
    username = forms.CharField(
        label=_('Email or Phone Number'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email or phone number',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # Basic validation
        if not username:
            raise ValidationError('Please enter your email or phone number.')
        
        return username


class CustomUserRegistrationForm(forms.ModelForm):
    """Form for user registration with no password validation"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name')
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        # Check for existing users
        if email and CustomUser.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        
        # Only check if passwords match
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        
        # Only check minimum length (4 characters)
        if password1 and len(password1) < 4:
            raise ValidationError('Password must be at least 4 characters long.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data["password1"]
        
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        
        return user