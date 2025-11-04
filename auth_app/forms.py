# from django import forms
# from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
# from django.utils.translation import gettext_lazy as _
# from django.core.validators import ValidationError
# from .models import CustomUser

# class CustomUserCreationForm(UserCreationForm):
#     """Form for creating new users with email or phone"""
    
#     class Meta:
#         model = CustomUser
#         fields = ('email', 'phone_number', 'first_name', 'last_name')
    
#     def clean(self):
#         cleaned_data = super().clean()
#         email = cleaned_data.get('email')
#         phone_number = cleaned_data.get('phone_number')
        
#         if not email and not phone_number:
#             raise ValidationError('Either email or phone number must be provided.')
        
#         return cleaned_data


# class CustomUserChangeForm(UserChangeForm):
#     """Form for updating users"""
    
#     class Meta:
#         model = CustomUser
#         fields = ('email', 'phone_number', 'first_name', 'last_name', 
#                  'timezone', 'email_notifications', 'push_notifications')


# class EmailOrPhoneAuthenticationForm(AuthenticationForm):
#     """Custom authentication form using email or phone number"""
    
#     username = forms.CharField(
#         label=_('Email or Phone Number'),
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter your email or phone number',
#             'autofocus': True
#         })
#     )
#     password = forms.CharField(
#         label=_('Password'),
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter your password'
#         })
#     )
    
#     def clean_username(self):
#         username = self.cleaned_data.get('username')
        
#         # Basic validation
#         if not username:
#             raise ValidationError('Please enter your email or phone number.')
        
#         return username


# class CustomUserRegistrationForm(UserCreationForm):
#     """Form for user registration with email or phone"""
    
#     email = forms.EmailField(
#         required=False,
#         widget=forms.EmailInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter your email (optional)'
#         })
#     )
#     phone_number = forms.CharField(
#         required=False,
#         max_length=17,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter your phone number (optional)'
#         })
#     )
#     first_name = forms.CharField(
#         max_length=30,
#         required=True,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter your first name'
#         })
#     )
#     last_name = forms.CharField(
#         max_length=30,
#         required=True,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter your last name'
#         })
#     )
#     password1 = forms.CharField(
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Create a password'
#         })
#     )
#     password2 = forms.CharField(
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Confirm your password'
#         })
#     )
    
#     class Meta:
#         model = CustomUser
#         fields = ('email', 'phone_number', 'first_name', 'last_name', 'password1', 'password2')
    
#     def clean(self):
#         cleaned_data = super().clean()
#         email = cleaned_data.get('email')
#         phone_number = cleaned_data.get('phone_number')
        
#         # Validate that at least one identifier is provided
#         if not email and not phone_number:
#             raise ValidationError('You must provide either an email address or phone number.')
        
#         # Check for existing users
#         if email and CustomUser.objects.filter(email=email).exists():
#             raise ValidationError('A user with this email already exists.')
        
#         if phone_number and CustomUser.objects.filter(phone_number=phone_number).exists():
#             raise ValidationError('A user with this phone number already exists.')
        
#         return cleaned_data
    
#     def save(self, commit=True):
#         user = super().save(commit=False)
        
#         # Ensure at least one identifier is set
#         if not user.email and not user.phone_number:
#             # This should not happen due to form validation, but just in case
#             raise ValueError("Either email or phone number must be provided")
        
#         if commit:
#             user.save()
        
#         return user