from django import forms
from django.utils import timezone
from .models import Task, MissedTaskReason

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'start_time', 'end_time', 'reminder_minutes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter task description (optional)'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'reminder_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 1440
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time")
            
            if start_time < timezone.now():
                raise forms.ValidationError("Start time cannot be in the past")
        
        return cleaned_data


class MissedTaskReasonForm(forms.ModelForm):
    """Form for adding custom missed task reasons"""
    
    class Meta:
        model = MissedTaskReason
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reason name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter description (optional)'
            }),
        }


class MarkAsNotDoneForm(forms.Form):
    """Form for marking task as not done with reason"""
    
    missed_reason = forms.ModelChoiceField(
        queryset=MissedTaskReason.objects.filter(is_active=True),
        required=False,
        empty_label="Select a reason...",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    custom_missed_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Or enter your own reason...'
        }),
        help_text="If you don't see a suitable reason above, you can write your own."
    )
    
    def clean(self):
        cleaned_data = super().clean()
        missed_reason = cleaned_data.get('missed_reason')
        custom_missed_reason = cleaned_data.get('custom_missed_reason')
        
        if not missed_reason and not custom_missed_reason:
            raise forms.ValidationError(
                "Please either select a reason or write your own reason for missing this task."
            )
        
        return cleaned_data