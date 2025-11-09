from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    """Admin configuration for custom user model"""
    
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    list_display = ('email', 'phone_number', 'first_name', 'last_name', 'is_staff', 'is_active', 'last_login_method')
    list_filter = ('is_staff', 'is_active', 'email_notifications', 'push_notifications', 'last_login_method')
    
    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'profile_picture')}),
        ('Preferences', {'fields': ('timezone', 'email_notifications', 'push_notifications')}),
        ('Login Information', {'fields': ('last_login_method', 'last_login', 'date_joined')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
    search_fields = ('email', 'phone_number', 'first_name', 'last_name')
    ordering = ('email',)
    
    def get_search_results(self, request, queryset, search_term):
        """Enable searching by both email and phone number"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        queryset |= self.model.objects.filter(phone_number__icontains=search_term)
        return queryset, use_distinct

admin.site.register(CustomUser, CustomUserAdmin)
