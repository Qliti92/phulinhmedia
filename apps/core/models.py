from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=120)
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def display_action(self):
        if self.action in ACTIVITY_ACTION_LABELS:
            return ACTIVITY_ACTION_LABELS[self.action]
        if self.action.startswith("POST "):
            return readable_request_action("POST", self.action[5:])
        if self.action.startswith("PUT "):
            return readable_request_action("PUT", self.action[4:])
        if self.action.startswith("PATCH "):
            return readable_request_action("PATCH", self.action[6:])
        if self.action.startswith("DELETE "):
            return readable_request_action("DELETE", self.action[7:])
        return self.action


class SystemSetting(models.Model):
    key = models.CharField(max_length=120, unique=True)
    value = models.TextField(blank=True)
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


ACTIVITY_ACTION_LABELS = {
    "task.created": "Tạo công việc mới",
    "task.updated": "Cập nhật công việc",
    "task.bulk_assigned": "Giao việc hàng loạt",
    "task.reviewed": "Duyệt kết quả công việc",
    "project.created": "Tạo dự án mới",
    "project.updated": "Cập nhật dự án",
    "project.bulk_updated": "Cập nhật hàng loạt dự án",
    "user.login": "Đăng nhập hệ thống",
    "user.logout": "Đăng xuất hệ thống",
}


def readable_request_action(method, path):
    clean_path = path.strip("/")
    if "cap-nhat-nhanh" in clean_path:
        return "Cập nhật nhanh công việc"
    if "giao-hang-loat" in clean_path:
        return "Giao việc hàng loạt"
    if clean_path.startswith("cong-viec/tao"):
        return "Tạo công việc mới"
    if clean_path.startswith("cong-viec") and method in {"POST", "PUT", "PATCH"}:
        return "Cập nhật công việc"
    if clean_path.startswith("du-an/bulk"):
        return "Cập nhật hàng loạt dự án"
    if clean_path.startswith("du-an/tao"):
        return "Tạo dự án mới"
    if clean_path.startswith("du-an") and method in {"POST", "PUT", "PATCH"}:
        return "Cập nhật dự án"
    if clean_path.startswith("tai-khoan"):
        return "Cập nhật tài khoản hoặc phân quyền"
    if clean_path.startswith("import"):
        return "Import dữ liệu dự án"
    if clean_path.startswith("thong-bao"):
        return "Cập nhật trạng thái thông báo"
    if clean_path.startswith("dang-xuat"):
        return "Đăng xuất hệ thống"
    return "Thực hiện thao tác trong hệ thống"
