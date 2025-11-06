from django.db import models
from django.conf import settings
from django.utils import timezone

class MissedTaskReason(models.Model):
    """Model for predefined reasons why tasks were missed"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Missed Task Reason"
        verbose_name_plural = "Missed Task Reasons"
        ordering = ['name']


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('not_done', 'Not Done'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reminder_minutes = models.IntegerField(default=10)
    
    # Reasons for missed tasks
    missed_reason = models.ForeignKey(
        MissedTaskReason, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Reason for missing task"
    )
    custom_missed_reason = models.TextField(
        blank=True, 
        verbose_name="Custom reason for missing task"
    )
    missed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        return self.end_time < timezone.now() and self.status != 'completed'
    
    @property
    def has_missed_reason(self):
        return bool(self.missed_reason or self.custom_missed_reason)
    
    def get_missed_reason_display(self):
        """Get the display text for missed reason"""
        if self.custom_missed_reason:
            return self.custom_missed_reason
        elif self.missed_reason:
            return self.missed_reason.name
        return "No reason provided"
    
    def mark_as_not_done(self, reason=None, custom_reason=""):
        """Mark task as not done with optional reason"""
        self.status = 'not_done'
        self.missed_at = timezone.now()
        
        if reason:
            self.missed_reason = reason
        if custom_reason:
            self.custom_missed_reason = custom_reason
            
        self.save()
    
    class Meta:
        ordering = ['start_time']
