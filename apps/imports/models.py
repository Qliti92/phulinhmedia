from django.conf import settings
from django.db import models


class ImportSession(models.Model):
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    original_file_name = models.CharField(max_length=255)
    total_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)
    duplicate_in_file = models.PositiveIntegerField(default=0)
    duplicate_in_system = models.PositiveIntegerField(default=0)
    imported_success = models.PositiveIntegerField(default=0)
    committed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ImportRow(models.Model):
    session = models.ForeignKey(ImportSession, on_delete=models.CASCADE, related_name="rows")
    row_number = models.PositiveIntegerField()
    raw_value = models.TextField()
    domain = models.CharField(max_length=255, blank=True)
    is_valid = models.BooleanField(default=False)
    is_duplicate_file = models.BooleanField(default=False)
    is_duplicate_system = models.BooleanField(default=False)
    error_message = models.CharField(max_length=255, blank=True)
    existing_project_id = models.PositiveIntegerField(null=True, blank=True)
    imported_project_id = models.PositiveIntegerField(null=True, blank=True)
