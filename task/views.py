from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Q
from datetime import datetime, timedelta
import json

from task.models import Task, MissedTaskReason
from task.forms import TaskForm, MarkAsNotDoneForm, MissedTaskReasonForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Q, Avg
from datetime import datetime, timedelta
from .models import Task, MissedTaskReason

@login_required(login_url='login')
def dashboard(request):
    # Auto-update task statuses for this user before showing data
    tasks_to_update = Task.objects.filter(
        user=request.user,
        end_time__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    )
    
    updated_count = 0
    for task in tasks_to_update:
        old_status = task.status
        new_status = task.auto_update_status()
        if old_status != new_status:
            updated_count += 1
    
    if updated_count > 0:
        messages.info(request, f"Automatically updated {updated_count} task statuses based on deadlines.")
    
    # Get current date and calculate date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Get user's tasks (after auto-update)
    tasks = Task.objects.filter(user=request.user)
    
    # Statistics
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    pending_tasks = tasks.filter(status='pending').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    not_done_tasks = tasks.filter(status='not_done').count()
    
    # Missed tasks with reasons analysis
    missed_with_reasons = tasks.filter(status='not_done', missed_reason__isnull=False).count()
    missed_with_custom_reasons = tasks.filter(status='not_done', custom_missed_reason__isnull=False).exclude(custom_missed_reason='').count()
    missed_without_reasons = tasks.filter(status='not_done', missed_reason__isnull=True, custom_missed_reason='').count()
    
    # Today's tasks
    today_tasks = tasks.filter(
        start_time__date=today
    ).order_by('start_time')
    
    # Upcoming tasks (next 7 days)
    upcoming_tasks = tasks.filter(
        start_time__date__gte=today,
        start_time__date__lte=today + timedelta(days=7)
    ).exclude(status__in=['completed', 'not_done']).order_by('start_time')[:5]
        
    # Overdue tasks (for notification)
    overdue_tasks = tasks.filter(
        end_time__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).count()
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'not_done_tasks': not_done_tasks,
        'missed_with_reasons': missed_with_reasons,
        'missed_with_custom_reasons': missed_with_custom_reasons,
        'missed_without_reasons': missed_without_reasons,
        'today_tasks': today_tasks,
        'upcoming_tasks': upcoming_tasks,
        'overdue_tasks': overdue_tasks,
        'auto_updated_count': updated_count,
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def task_list(request):
    # Auto-update task statuses for this user before showing data
    tasks_to_update = Task.objects.filter(
        user=request.user,
        end_time__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    )
    
    updated_count = 0
    for task in tasks_to_update:
        old_status = task.status
        new_status = task.auto_update_status()
        if old_status != new_status:
            updated_count += 1
    
    if updated_count > 0:
        messages.info(request, f"Automatically updated {updated_count} task statuses.")
    
    status_filter = request.GET.get('status', 'all')
    
    tasks = Task.objects.filter(user=request.user)
    
    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    
    # Sort by start time (upcoming first)
    tasks = tasks.order_by('start_time')
    
    context = {
        'tasks': tasks,
        'status_filter': status_filter,
        'auto_updated_count': updated_count,
    }
    
    return render(request, 'task_list.html', context)
@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, 'Task created successfully!')
            return redirect('task_list')
    else:
        form = TaskForm()
    
    return render(request, 'task_form.html', {'form': form, 'title': 'Create Task'})

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully!')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'task_form.html', {'form': form, 'title': 'Edit Task'})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('task_list')
    
    return render(request, 'task_confirm_delete.html', {'task': task})

@login_required
def update_task_status(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id, user=request.user)
        new_status = request.POST.get('status')
        
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.save()
            messages.success(request, f'Task status updated to {task.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('task_list')

@login_required
def mark_task_not_done(request, task_id):
    """Mark a task as not done with reason"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = MarkAsNotDoneForm(request.POST)
        if form.is_valid():
            missed_reason = form.cleaned_data.get('missed_reason')
            custom_reason = form.cleaned_data.get('custom_missed_reason', '')
            
            task.mark_as_not_done(reason=missed_reason, custom_reason=custom_reason)
            
            messages.success(request, f'Task "{task.title}" marked as not done. Reason recorded.')
            return redirect('task_list')
    else:
        form = MarkAsNotDoneForm()
    
    return render(request, 'tasks/mark_not_done.html', {
        'task': task,
        'form': form
    })

@login_required
def add_missed_reason(request, task_id):
    """Add reason to an already missed task"""
    task = get_object_or_404(Task, id=task_id, user=request.user, status='not_done')
    
    if request.method == 'POST':
        form = MarkAsNotDoneForm(request.POST)
        if form.is_valid():
            missed_reason = form.cleaned_data.get('missed_reason')
            custom_reason = form.cleaned_data.get('custom_missed_reason', '')
            
            task.missed_reason = missed_reason
            task.custom_missed_reason = custom_reason
            task.save()
            
            messages.success(request, f'Reason added to task "{task.title}".')
            return redirect('task_list')
    else:
        form = MarkAsNotDoneForm()
    
    return render(request, 'tasks/add_missed_reason.html', {
        'task': task,
        'form': form
    })

@login_required
def missed_tasks_analysis(request):
    """View for analyzing missed tasks with reasons"""
    date_range = request.GET.get('range', '30days')
    
    if date_range == '7days':
        days = 7
    elif date_range == '90days':
        days = 90
    else:
        days = 30
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get missed tasks in date range
    missed_tasks = Task.objects.filter(
        user=request.user,
        status='not_done',
        end_time__date__gte=start_date,
        end_time__date__lte=end_date
    )
    
    # Reason analysis
    reason_stats = missed_tasks.filter(missed_reason__isnull=False).values(
        'missed_reason__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Tasks without reasons
    tasks_without_reasons = missed_tasks.filter(
        missed_reason__isnull=True, 
        custom_missed_reason=''
    )
    
    # Common custom reasons (top 10)
    common_custom_reasons = missed_tasks.filter(
        custom_missed_reason__isnull=False
    ).exclude(
        custom_missed_reason=''
    ).values(
        'custom_missed_reason'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'missed_tasks': missed_tasks,
        'reason_stats': reason_stats,
        'tasks_without_reasons': tasks_without_reasons,
        'common_custom_reasons': common_custom_reasons,
        'date_range': date_range,
        'days': days,
        'total_missed': missed_tasks.count(),
    }
    
    return render(request, 'tasks/missed_tasks_analysis.html', context)

@login_required
def manage_missed_reasons(request):
    """View for managing missed task reasons (admin-like functionality for users)"""
    if request.method == 'POST':
        form = MissedTaskReasonForm(request.POST)
        if form.is_valid():
            reason = form.save()
            messages.success(request, f'Reason "{reason.name}" added successfully!')
            return redirect('manage_missed_reasons')
    else:
        form = MissedTaskReasonForm()
    
    # Get all active reasons
    reasons = MissedTaskReason.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'reasons': reasons,
    }
    
    return render(request, 'tasks/manage_missed_reasons.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
import json
from .models import Task, MissedTaskReason

@login_required
def analytics(request):
    """Comprehensive analytics dashboard"""
    # Date range filter
    date_range = request.GET.get('range', '30days')
    
    if date_range == '7days':
        days = 7
    elif date_range == '90days':
        days = 90
    else:
        days = 30
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get user's tasks in the date range
    tasks = Task.objects.filter(
        user=request.user,
        start_time__date__gte=start_date,
        start_time__date__lte=end_date
    )
    
    # Basic statistics
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    pending_tasks = tasks.filter(status='pending').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    not_done_tasks = tasks.filter(status='not_done').count()
    
    # Completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Status distribution for chart
    status_distribution = tasks.values('status').annotate(count=Count('id'))
    status_data = {
        'labels': [],
        'data': [],
        'colors': ['#4361ee', '#4cc9f0', '#f72585', '#e63946']
    }
    
    for status in status_distribution:
        status_data['labels'].append(dict(Task.STATUS_CHOICES)[status['status']])
        status_data['data'].append(status['count'])
    
    # Daily completion trend
    daily_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        day_tasks = tasks.filter(start_time__date=date)
        completed = day_tasks.filter(status='completed').count()
        total = day_tasks.count()
        
        if total > 0:
            day_completion_rate = (completed / total) * 100
        else:
            day_completion_rate = 0
            
        daily_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'completion_rate': day_completion_rate,
            'total_tasks': total,
            'completed_tasks': completed
        })
    
    # Task duration analysis - FIXED: Calculate duration in Python instead of database
    completed_tasks_with_duration = tasks.filter(
        status='completed',
        start_time__isnull=False,
        end_time__isnull=False
    )
    
    # Calculate average duration manually
    total_duration_hours = 0
    valid_tasks_count = 0
    
    for task in completed_tasks_with_duration:
        if task.start_time and task.end_time:
            duration = task.end_time - task.start_time
            total_duration_hours += duration.total_seconds() / 3600
            valid_tasks_count += 1
    
    avg_duration = total_duration_hours / valid_tasks_count if valid_tasks_count > 0 else 0
    
    # Most productive days
    productive_days = tasks.filter(status='completed').values(
        'start_time__week_day'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:3]
    
    day_names = {
        1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday',
        5: 'Friday', 6: 'Saturday', 7: 'Sunday'
    }
    
    productive_days_list = []
    for day in productive_days:
        productive_days_list.append({
            'day': day_names[day['start_time__week_day']],
            'count': day['count']
        })
    
    # Missed tasks analysis
    missed_tasks = tasks.filter(status='not_done')
    missed_with_reasons = missed_tasks.filter(
        Q(missed_reason__isnull=False) | ~Q(custom_missed_reason='')
    ).count()
    
    missed_reason_stats = missed_tasks.filter(
        missed_reason__isnull=False
    ).values('missed_reason__name').annotate(count=Count('id')).order_by('-count')[:5]
    
    context = {
        'date_range': date_range,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        
        # Statistics
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'not_done_tasks': not_done_tasks,
        'completion_rate': round(completion_rate, 1),
        
        # Chart data
        'status_data': status_data,
        'daily_data': daily_data,
        
        # Advanced analytics
        'avg_duration': round(avg_duration, 1),
        'productive_days': productive_days_list,
        'missed_with_reasons': missed_with_reasons,
        'missed_reason_stats': list(missed_reason_stats),
        
        # Time ranges for filter
        'time_ranges': [
            {'value': '7days', 'label': 'Last 7 Days'},
            {'value': '30days', 'label': 'Last 30 Days'},
            {'value': '90days', 'label': 'Last 90 Days'},
        ]
    }
    
    return render(request, 'analytics/analytics.html', context)

@login_required
def get_tasks_json(request):
    """API endpoint for task data in JSON format"""
    date_range = request.GET.get('range', '30days')
    
    if date_range == '7days':
        days = 7
    elif date_range == '90days':
        days = 90
    else:
        days = 30
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    tasks = Task.objects.filter(
        user=request.user,
        start_time__date__gte=start_date,
        start_time__date__lte=end_date
    ).order_by('start_time')
    
    tasks_data = []
    for task in tasks:
        # Calculate duration manually
        duration_hours = 0
        if task.start_time and task.end_time:
            duration = task.end_time - task.start_time
            duration_hours = round(duration.total_seconds() / 3600, 2)
        
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'start_time': task.start_time.isoformat(),
            'end_time': task.end_time.isoformat(),
            'status': task.status,
            'status_display': task.get_status_display(),
            'duration_hours': duration_hours,
            'is_overdue': task.is_overdue,
            'has_missed_reason': task.has_missed_reason,
            'missed_reason': task.get_missed_reason_display() if task.has_missed_reason else None,
        })
    
    return JsonResponse({
        'tasks': tasks_data,
        'meta': {
            'total_count': len(tasks_data),
            'date_range': f"{start_date} to {end_date}",
            'generated_at': timezone.now().isoformat()
        }
    })

@login_required
def productivity_metrics(request):
    """Detailed productivity metrics API"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)  # Last 30 days
    
    tasks = Task.objects.filter(
        user=request.user,
        start_time__date__gte=start_date,
        start_time__date__lte=end_date
    )
    
    # Weekly completion rates
    weekly_data = []
    for week in range(4):
        week_start = end_date - timedelta(days=(week + 1) * 7)
        week_end = end_date - timedelta(days=week * 7)
        
        week_tasks = tasks.filter(
            start_time__date__gte=week_start,
            start_time__date__lt=week_end
        )
        week_completed = week_tasks.filter(status='completed').count()
        week_total = week_tasks.count()
        
        weekly_data.append({
            'week': f"Week {4 - week}",
            'completed': week_completed,
            'total': week_total,
            'rate': round((week_completed / week_total * 100) if week_total > 0 else 0, 1)
        })
    
    # Task completion time analysis - FIXED
    completed_tasks = tasks.filter(status='completed')
    completion_times = []
    
    for task in completed_tasks:
        if task.start_time and task.end_time:
            completion_time = (task.end_time - task.start_time).total_seconds() / 3600
            completion_times.append(completion_time)
    
    if completion_times:
        avg_completion_time = sum(completion_times) / len(completion_times)
        min_completion_time = min(completion_times)
        max_completion_time = max(completion_times)
    else:
        avg_completion_time = min_completion_time = max_completion_time = 0
    
    return JsonResponse({
        'weekly_data': weekly_data,
        'completion_times': {
            'average': round(avg_completion_time, 2),
            'min': round(min_completion_time, 2),
            'max': round(max_completion_time, 2),
        },
        'time_period': f"{start_date} to {end_date}"
    })
