from celery import shared_task
from django.utils import timezone

from apps.core.backups import create_backup, prune_old_backups
from apps.core.services import notify_user
from apps.notifications.models import Notification
from apps.projects.models import Project
from apps.tasks.models import Task


@shared_task
def create_daily_backup():
    path = create_backup(prefix="daily")
    prune_old_backups(keep=14)
    return str(path)


@shared_task
def check_deadlines():
    today = timezone.localdate()
    warning_day = today + timezone.timedelta(days=3)
    for project in Project.objects.exclude(status=Project.Status.DONE):
        if project.deadline and project.deadline < today and project.staff:
            notify_user(project.staff, "Dự án quá hạn", f"Dự án \"{project.domain}\" đã quá hạn.", url=f"/du-an/{project.pk}/", event_type=Notification.EventType.PROJECT_DEADLINE, priority=Notification.Priority.HIGH, channel=Notification.Channel.BOTH)
        elif project.deadline == warning_day and project.staff:
            notify_user(project.staff, "Dự án sắp đến hạn", f"Dự án \"{project.domain}\" còn 3 ngày đến hạn.", url=f"/du-an/{project.pk}/", event_type=Notification.EventType.PROJECT_DEADLINE, priority=Notification.Priority.NORMAL)

    for task in Task.objects.exclude(status=Task.Status.DONE):
        if task.deadline and task.deadline < today and task.assignee:
            notify_user(task.assignee, "Công việc quá hạn", f"Công việc \"{task.title}\" đã quá hạn.", url=f"/cong-viec/{task.pk}/", event_type=Notification.EventType.TASK_DEADLINE, priority=Notification.Priority.HIGH, channel=Notification.Channel.BOTH)
        elif task.deadline == warning_day and task.assignee:
            notify_user(task.assignee, "Công việc sắp đến hạn", f"Công việc \"{task.title}\" còn 3 ngày đến hạn.", url=f"/cong-viec/{task.pk}/", event_type=Notification.EventType.TASK_DEADLINE, priority=Notification.Priority.NORMAL)
