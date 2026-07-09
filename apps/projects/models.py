from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.accounts.models import ManagerStaffRelation, User
from .utils import is_valid_domain, normalize_domain


class ProjectQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_admin_role:
            return self
        if user.is_manager_role:
            return self.filter(manager=user)
        return self.filter(staff=user)


class Project(models.Model):
    class Status(models.TextChoices):
        UNASSIGNED = "unassigned", "Chưa giao"
        ASSIGNED = "assigned", "Đã giao"
        IN_PROGRESS = "in_progress", "Đang làm"
        DONE = "done", "Hoàn thành"

    class ProgressStage(models.TextChoices):
        REVIEW = "review", "Chờ duyệt"
        REGISTERED = "registered", "ĐK thành công"
        CAMPAIGN_SET = "campaign_set", "Đã set camp"
        SPENT = "spent", "Đã chi tiêu"

    PROGRESS_BY_STAGE = {
        ProgressStage.REVIEW: 25,
        ProgressStage.REGISTERED: 50,
        ProgressStage.CAMPAIGN_SET: 75,
        ProgressStage.SPENT: 100,
    }

    domain = models.CharField("Domain", max_length=255, unique=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_projects", limit_choices_to={"role": User.Role.MANAGER}, verbose_name="Manager")
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_projects", limit_choices_to={"role": User.Role.STAFF}, verbose_name="Nhân viên")
    status = models.CharField("Trạng thái giao việc", max_length=30, choices=Status.choices, default=Status.UNASSIGNED)
    progress_stage = models.CharField("Trạng thái tiến trình", max_length=30, choices=ProgressStage.choices, blank=True)
    progress = models.PositiveSmallIntegerField("Tiến độ (%)", default=0)
    campaign_link = models.URLField("Link camp", blank=True)
    registration_link_1 = models.URLField("Link đăng ký", blank=True)
    registration_link_2 = models.URLField("Link đăng ký 2", blank=True)
    registration_link_3 = models.URLField("Link đăng ký 3", blank=True)
    deadline = models.DateField("Deadline", null=True, blank=True)
    note = models.TextField("Ghi chú", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_projects", verbose_name="Người tạo")
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật", auto_now=True)

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        self.domain = normalize_domain(self.domain)
        if not is_valid_domain(self.domain):
            from django.core.exceptions import ValidationError

            raise ValidationError({"domain": "Domain không hợp lệ"})
        if self.staff and self.manager:
            relation_exists = ManagerStaffRelation.objects.filter(manager=self.manager, staff=self.staff).exists()
            if not relation_exists:
                from django.core.exceptions import ValidationError

                raise ValidationError("Nhân viên này không thuộc manager đã chọn")

    def save(self, *args, **kwargs):
        self.domain = normalize_domain(self.domain)
        if self.progress_stage:
            self.progress = self.PROGRESS_BY_STAGE.get(self.progress_stage, self.progress)
        self.progress = min(max(self.progress, 0), 100)
        if self.staff and self.status == self.Status.UNASSIGNED:
            self.status = self.Status.ASSIGNED
        if self.progress >= 100:
            self.status = self.Status.DONE
        super().save(*args, **kwargs)

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
        return self.domain
