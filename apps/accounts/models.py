from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email là bắt buộc")
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        STAFF = "staff", "Staff"

    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField("Họ tên", max_length=180)
    role = models.CharField("Vai trò", max_length=20, choices=Role.choices, default=Role.STAFF)
    telegram_chat_id = models.CharField("Telegram Chat ID", max_length=80, blank=True)
    is_locked = models.BooleanField("Đã khóa", default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]
    objects = UserManager()

    class Meta:
        ordering = ["full_name", "email"]

    def __str__(self):
        return self.full_name or self.email

    @property
    def is_admin_role(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def is_manager_role(self):
        return self.role == self.Role.MANAGER

    @property
    def is_staff_role(self):
        return self.role == self.Role.STAFF


class ManagerStaffRelation(models.Model):
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name="managed_staff", limit_choices_to={"role": User.Role.MANAGER})
    staff = models.OneToOneField(User, on_delete=models.CASCADE, related_name="manager_relation", limit_choices_to={"role": User.Role.STAFF})
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Quan hệ quản lý - nhân viên"
        verbose_name_plural = "Quan hệ quản lý - nhân viên"

    def __str__(self):
        return f"{self.manager} quản lý {self.staff}"
