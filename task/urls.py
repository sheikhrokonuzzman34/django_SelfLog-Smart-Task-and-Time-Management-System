from django.urls import path
from task import views
from task.views import *


urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('tasks/', task_list, name='task_list'),
    path('tasks/create/', create_task, name='create_task'),
    path('tasks/<int:task_id>/edit/', edit_task, name='edit_task'),
    path('tasks/<int:task_id>/delete/', delete_task, name='delete_task'),
    path('tasks/<int:task_id>/update-status/', update_task_status, name='update_task_status'),

    # Missed task reasons
    path('tasks/<int:task_id>/mark-not-done/', mark_task_not_done, name='mark_task_not_done'),
    path('tasks/<int:task_id>/add-missed-reason/',add_missed_reason, name='add_missed_reason'),
    path('analytics/missed-tasks/', missed_tasks_analysis, name='missed_tasks_analysis'),
    path('analytics/missed-reasons/', manage_missed_reasons, name='manage_missed_reasons'),
    
    # Analytics
    path('analytics/',analytics, name='analytics'),
    path('api/tasks/',get_tasks_json, name='get_tasks_json'),
    path('api/productivity-metrics/', productivity_metrics, name='productivity_metrics'),
]