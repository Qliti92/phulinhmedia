from django.conf import settings
from django.db import models


class Notification(models.Model):
    class EventType(models.TextChoices):
        TASK_ASSIGNED = "task_assigned", "Giao công việc"
        TASK_UPDATED = "task_updated", "Cập nhật công việc"
        TASK_BLOCKED = "task_blocked", "Công việc vướng mắc"
        TASK_DONE = "task_done", "Hoàn thành công việc"
        TASK_REVIEWED = "task_reviewed", "Duyệt công việc"
        TASK_DEADLINE = "task_deadline", "Nhắc deadline công việc"
        PROJECT_ASSIGNED = "project_assigned", "Giao dự án"
        PROJECT_UPDATED = "project_updated", "Cập nhật dự án"
        PROJECT_DEADLINE = "project_deadline", "Nhắc deadline dự án"
        SYSTEM = "system", "Hệ thống"

    class Priority(models.TextChoices):
        LOW = "low", "Thấp"
        NORMAL = "normal", "Bình thường"
        HIGH = "high", "Quan trọng"

    class Channel(models.TextChoices):
        IN_APP = "in_app", "Trong hệ thống"
        TELEGRAM = "telegram", "Telegram"
        BOTH = "both", "Hệ thống + Telegram"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=180)
    message = models.TextField()
    url = models.CharField(max_length=255, blank=True)
    event_type = models.CharField(max_length=40, choices=EventType.choices, default=EventType.SYSTEM)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.IN_APP)
    is_read = models.BooleanField(default=False)
    telegram_sent_at = models.DateTimeField(null=True, blank=True)
    telegram_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.title}"
