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
    
    def save(self, *args, **kwargs):
        """Override save method to automatically update status based on end_time"""
        # Check if end_time has passed
        if self.end_time and self.end_time < timezone.now():
            if self.status == 'pending':
                # If status is pending and end_time is over, mark as not_done
                self.status = 'not_done'
                self.missed_at = timezone.now()
            elif self.status == 'in_progress':
                # If status is in_progress and end_time is over, mark as completed
                self.status = 'completed'
        
        super().save(*args, **kwargs)
    
    @property
    def task_miss(self):
        """Check if task should be marked as missed"""
        if self.end_time < timezone.now() and self.status != 'completed':
            # Auto-update status if needed
            if self.status == 'pending':
                self.status = 'not_done'
                self.missed_at = timezone.now()
                self.save()
            elif self.status == 'in_progress':
                self.status = 'completed'
                self.save()
            return True
        return False
    
    @property
    def is_overdue(self):
        """Check if task is overdue (end_time passed but not completed)"""
        return self.end_time < timezone.now() and self.status not in ['completed', 'not_done']
    
    @property
    def should_auto_update(self):
        """Check if task status should be automatically updated"""
        return self.end_time < timezone.now() and self.status in ['pending', 'in_progress']
    
    def auto_update_status(self):
        """Automatically update status based on current time and end_time"""
        if self.end_time < timezone.now():
            if self.status == 'pending':
                self.mark_as_not_done()
                return 'not_done'
            elif self.status == 'in_progress':
                self.status = 'completed'
                self.save()
                return 'completed'
        return self.status
    
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