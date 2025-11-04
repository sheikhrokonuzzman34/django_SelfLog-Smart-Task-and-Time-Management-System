from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class CustomUserManager(BaseUserManager):
    """Custom user manager for email or phone number authentication"""
    
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        """Create and return a regular user with email/phone and password"""
        if not email and not phone_number:
            raise ValueError(_('Either Email or Phone Number must be set'))
        
        if email:
            email = self.normalize_email(email)
        
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password=password, **extra_fields)

    def get_by_natural_key(self, username):
        """Allow login with either email or phone number"""
        return self.get(
            models.Q(email=username) | 
            models.Q(phone_number=username)
        )


class CustomUser(AbstractUser):
    """Custom user model with email or phone number as username"""
    
    username = None
    
    # Phone number validator
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    email = models.EmailField(
        _('email address'), 
        unique=True, 
        blank=True, 
        null=True
    )
    phone_number = models.CharField(
        _('phone number'),
        validators=[phone_regex],
        max_length=17,
        unique=True,
        blank=True,
        null=True
    )
    
    # Additional fields
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    timezone = models.CharField(max_length=50, default='Asia/Dhaka')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Login method tracking
    last_login_method = models.CharField(
        max_length=10,
        choices=[('email', 'Email'), ('phone', 'Phone')],
        blank=True,
        null=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email or self.phone_number or f"User {self.id}"

    def get_username(self):
        """Return the identifier used for authentication"""
        return self.email or self.phone_number

    def clean(self):
        """Validate that at least one of email or phone number is provided"""
        from django.core.exceptions import ValidationError
        if not self.email and not self.phone_number:
            raise ValidationError('Either email or phone number must be provided.')

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')