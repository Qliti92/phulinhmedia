from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.accounts.models import ManagerStaffRelation, User
from apps.projects.models import Project


class TaskQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_admin_role:
            return self
        if user.is_manager_role:
            staff_ids = ManagerStaffRelation.objects.filter(manager=user).values_list("staff_id", flat=True)
            return self.filter(models.Q(created_by=user) | models.Q(assignee=user) | models.Q(assignee_id__in=staff_ids))
        return self.filter(assignee=user)


class Task(models.Model):
    class Status(models.TextChoices):
        UNASSIGNED = "unassigned", "Chưa giao"
        ASSIGNED = "assigned", "Đã giao"
        IN_PROGRESS = "in_progress", "Đang làm"
        BLOCKED = "blocked", "Vướng mắc"
        DONE = "done", "Hoàn thành"

    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks", verbose_name="Dự án")
    title = models.CharField("Tiêu đề", max_length=220)
    description = models.TextField("Mô tả", blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_tasks", limit_choices_to={"role__in": [User.Role.MANAGER, User.Role.STAFF]}, verbose_name="Người nhận")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_tasks", verbose_name="Người tạo")
    status = models.CharField("Trạng thái", max_length=30, choices=Status.choices, default=Status.UNASSIGNED)
    progress_stage = models.CharField("Trạng thái tiến trình", max_length=30, blank=True)
    progress = models.PositiveSmallIntegerField("Tiến độ (%)", default=0)
    blocker_note = models.TextField("Vướng mắc", blank=True)
    completion_note = models.TextField("Ghi chú cập nhật", blank=True)
    deadline = models.DateField("Deadline", null=True, blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật", auto_now=True)

    objects = TaskQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.created_by and self.created_by.is_manager_role and self.assignee and self.assignee.is_staff_role:
            relation_exists = ManagerStaffRelation.objects.filter(manager=self.created_by, staff=self.assignee).exists()
            if not relation_exists:
                from django.core.exceptions import ValidationError

                raise ValidationError("Nhân viên không thuộc manager này")

    def save(self, *args, **kwargs):
        self.progress = min(max(self.progress, 0), 100)
        if self.assignee and self.status == self.Status.UNASSIGNED:
            self.status = self.Status.ASSIGNED
        if self.progress >= 100:
            self.status = self.Status.DONE
        elif self.blocker_note and self.status == self.Status.IN_PROGRESS:
            self.status = self.Status.BLOCKED
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return bool(self.deadline and self.deadline < timezone.localdate() and self.status != self.Status.DONE)

    @property
    def deadline_state_label(self):
        if not self.deadline:
            return "Chưa đặt hạn"
        if self.status == self.Status.DONE:
            return "Đã hoàn thành"
        days = (self.deadline - timezone.localdate()).days
        if days < 0:
            return f"Quá hạn {abs(days)} ngày"
        if days == 0:
            return "Đến hạn hôm nay"
        if days <= 3:
            return f"Sắp đến hạn, còn {days} ngày"
        return f"Còn {days} ngày"

    @property
    def deadline_state_class(self):
        if not self.deadline:
            return "deadline-muted"
        if self.status == self.Status.DONE:
            return "deadline-done"
        days = (self.deadline - timezone.localdate()).days
        if days < 0:
            return "deadline-overdue"
        if days <= 3:
            return "deadline-warning"
        return "deadline-ok"

    def __str__(self):
        return self.title


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to="task-attachments/%Y/%m/")
    note = models.CharField("Ghi chú", max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class StaffPerformance(models.Model):
    staff = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="performance", limit_choices_to={"role": User.Role.STAFF})
    total_assigned = models.PositiveIntegerField(default=0)
    total_done = models.PositiveIntegerField(default=0)
    on_time_done = models.PositiveIntegerField(default=0)
    overdue = models.PositiveIntegerField(default=0)
    returned_for_fix = models.PositiveIntegerField(default=0)
    blocked = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def recalculate(self):
        qs = self.staff.assigned_tasks.all()
        today = timezone.localdate()
        self.total_assigned = qs.count()
        self.total_done = qs.filter(status=Task.Status.DONE).count()
        self.overdue = qs.filter(deadline__lt=today).exclude(status=Task.Status.DONE).count()
        self.blocked = qs.filter(status=Task.Status.BLOCKED).count()
        self.returned_for_fix = 0
        self.completion_rate = (self.total_done / self.total_assigned * 100) if self.total_assigned else 0
        self.score = max(0, self.completion_rate + self.on_time_done * 2 - self.overdue * 5 - self.blocked * 2)
        self.save()


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Có mặt"
        LATE = "late", "Đi muộn"
        ABSENT = "absent", "Vắng"
        LEAVE = "leave", "Nghỉ phép"

    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_records", limit_choices_to={"role": User.Role.STAFF})
    date = models.DateField(default=timezone.localdate)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_attendance_records")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "staff__full_name"]
        unique_together = ["staff", "date"]

    def __str__(self):
        return f"{self.staff} - {self.date}"
