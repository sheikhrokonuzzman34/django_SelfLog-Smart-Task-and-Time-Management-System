from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserRegistrationForm, CustomUserChangeForm, EmailOrPhoneAuthenticationForm
from .models import CustomUser

def register(request):
    """Handle user registration with email or phone"""
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Auto-login after registration
            login(request, user)
            
            # Determine login method for message
            if user.email:
                identifier = user.email
            else:
                identifier = user.phone_number
                
            messages.success(request, f'Registration successful! Welcome to SelfLog, {user.first_name}.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    """Handle user profile view and update"""
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            
            # Show which identifier was updated
            if 'email' in form.changed_data:
                messages.success(request, 'Email updated successfully!')
            elif 'phone_number' in form.changed_data:
                messages.success(request, 'Phone number updated successfully!')
            else:
                messages.success(request, 'Profile updated successfully!')
                
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    # Get login statistics
    login_stats = {
        'total_logins': request.user.last_login,
        'last_method': request.user.last_login_method,
    }
    
    return render(request, 'registration/profile.html', {
        'form': form,
        'login_stats': login_stats
    })


def custom_login(request):
    """Custom login view with enhanced functionality"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EmailOrPhoneAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Determine login method for message
                if '@' in username:
                    login_method = 'email'
                    identifier = username
                else:
                    login_method = 'phone'
                    identifier = f"phone number ending in {username[-4:]}"
                
                messages.success(request, f'Welcome back! Signed in with {login_method}.')
                
                # Redirect to next page or dashboard
                next_page = request.GET.get('next', 'dashboard')
                return redirect(next_page)
    else:
        form = EmailOrPhoneAuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})


@login_required
def account_settings(request):
    """Advanced account settings page"""
    user = request.user
    
    if request.method == 'POST':
        # Handle different settings actions
        action = request.POST.get('action')
        
        if action == 'update_profile':
            form = CustomUserChangeForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
        
        elif action == 'update_preferences':
            email_notifications = request.POST.get('email_notifications') == 'on'
            push_notifications = request.POST.get('push_notifications') == 'on'
            timezone = request.POST.get('timezone')
            
            user.email_notifications = email_notifications
            user.push_notifications = push_notifications
            user.timezone = timezone
            user.save()
            
            messages.success(request, 'Preferences updated successfully!')
    
    # Common timezones for dropdown
    common_timezones = [
        'Asia/Dhaka', 'UTC', 'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific',
        'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Asia/Tokyo',
        'Asia/Shanghai', 'Asia/Kolkata', 'Australia/Sydney'
    ]
    
    context = {
        'common_timezones': common_timezones,
        'last_login_method': user.last_login_method,
    }
    
    return render(request, 'registration/account_settings.html', context)