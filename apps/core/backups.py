import json
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.db import transaction
from django.utils import timezone


BACKUP_APPS = [
    "accounts",
    "core",
    "projects",
    "tasks",
    "imports",
    "notifications",
]

RESTORE_DELETE_ORDER = [
    ("notifications", "Notification"),
    ("core", "ActivityLog"),
    ("imports", "ImportRow"),
    ("imports", "ImportSession"),
    ("tasks", "TaskAttachment"),
    ("tasks", "Attendance"),
    ("tasks", "StaffPerformance"),
    ("tasks", "Task"),
    ("projects", "Project"),
    ("accounts", "ManagerStaffRelation"),
    ("accounts", "User"),
    ("core", "SystemSetting"),
]

WIPE_OPERATIONAL_ORDER = [
    ("notifications", "Notification"),
    ("core", "ActivityLog"),
    ("imports", "ImportRow"),
    ("imports", "ImportSession"),
    ("tasks", "TaskAttachment"),
    ("tasks", "Attendance"),
    ("tasks", "StaffPerformance"),
    ("tasks", "Task"),
    ("projects", "Project"),
]


def backup_dir():
    path = Path(settings.BASE_DIR) / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_backup(prefix="manual"):
    timestamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
    path = backup_dir() / f"{prefix}-{timestamp}.json"
    with path.open("w", encoding="utf-8") as backup_file:
        call_command(
            "dumpdata",
            *BACKUP_APPS,
            "--natural-foreign",
            "--natural-primary",
            indent=2,
            stdout=backup_file,
        )
    return path


def list_backups():
    backups = []
    for path in backup_dir().glob("*.json"):
        backups.append({
            "name": path.name,
            "path": path,
            "size": path.stat().st_size,
            "created_at": timezone.datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.get_current_timezone()),
        })
    return sorted(backups, key=lambda item: item["created_at"], reverse=True)


def backup_path(filename):
    candidate = (backup_dir() / filename).resolve()
    root = backup_dir().resolve()
    if root not in candidate.parents or candidate.suffix.lower() != ".json":
        raise ValueError("File backup không hợp lệ.")
    if not candidate.exists():
        raise FileNotFoundError("Không tìm thấy file backup.")
    return candidate


def save_uploaded_backup(uploaded_file):
    if not uploaded_file.name.lower().endswith(".json"):
        raise ValueError("Chỉ hỗ trợ file backup .json.")
    timestamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
    safe_name = Path(uploaded_file.name).name.replace(" ", "-")
    path = backup_dir() / f"upload-{timestamp}-{safe_name}"
    with path.open("wb") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    with path.open("r", encoding="utf-8") as backup_file:
        json.load(backup_file)
    return path


def prune_old_backups(keep=14):
    backups = list_backups()
    for item in backups[keep:]:
        item["path"].unlink(missing_ok=True)


def restore_backup(filename):
    path = backup_path(filename)
    with path.open("r", encoding="utf-8") as backup_file:
        json.load(backup_file)
    with transaction.atomic():
        for app_label, model_name in RESTORE_DELETE_ORDER:
            apps.get_model(app_label, model_name).objects.all().delete()
        call_command("loaddata", str(path), verbosity=0)
    return path


def wipe_operational_data():
    deleted = {}
    with transaction.atomic():
        for app_label, model_name in WIPE_OPERATIONAL_ORDER:
            model = apps.get_model(app_label, model_name)
            count, _ = model.objects.all().delete()
            deleted[f"{app_label}.{model_name}"] = count
    return deleted
