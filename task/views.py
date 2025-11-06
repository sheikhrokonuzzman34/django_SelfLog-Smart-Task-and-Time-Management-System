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

@login_required
def dashboard(request):
    # Get current date and calculate date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Get user's tasks
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
    ).exclude(status='completed').order_by('start_time')[:5]
    
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
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def task_list(request):
    status_filter = request.GET.get('status', 'all')
    
    tasks = Task.objects.filter(user=request.user)
    
    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    
    # Sort by start time (upcoming first)
    tasks = tasks.order_by('start_time')
    
    context = {
        'tasks': tasks,
        'status_filter': status_filter,
    }
    
    return render(request, 'task_list.html', context)



@login_required
def task_list(request):
    status_filter = request.GET.get('status', 'all')
    
    tasks = Task.objects.filter(user=request.user)
    
    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    
    tasks = tasks.order_by('start_time')
    
    context = {
        'tasks': tasks,
        'status_filter': status_filter,
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

# ... (keep the existing view functions: create_task, edit_task, delete_task, update_task_status, analytics, get_tasks_json)
