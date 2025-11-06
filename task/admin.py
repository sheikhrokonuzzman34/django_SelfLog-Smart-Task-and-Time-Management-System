from django.contrib import admin
from .models import Task, MissedTaskReason

@admin.register(MissedTaskReason)
class MissedTaskReasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    actions = ['activate_reasons', 'deactivate_reasons']
    
    def activate_reasons(self, request, queryset):
        queryset.update(is_active=True)
    activate_reasons.short_description = "Activate selected reasons"
    
    def deactivate_reasons(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_reasons.short_description = "Deactivate selected reasons"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'start_time', 'end_time', 'status', 'has_missed_reason')
    list_filter = ('status', 'missed_reason', 'start_time', 'created_at')
    search_fields = ('title', 'description', 'custom_missed_reason')
    readonly_fields = ('created_at', 'updated_at', 'missed_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'reminder_minutes')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Missed Task Details', {
            'fields': ('missed_reason', 'custom_missed_reason', 'missed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )