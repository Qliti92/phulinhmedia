import json
from urllib import request as urlrequest

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.models import ManagerStaffRelation, User
from apps.core.backups import backup_path, create_backup, list_backups, restore_backup, save_uploaded_backup, wipe_operational_data
from apps.core.forms import RestoreBackupForm, SystemMaintenanceForm, UploadBackupForm, WipeDataForm
from apps.core.models import ActivityLog
from apps.projects.models import Project
from apps.tasks.models import StaffPerformance, Task


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        projects = Project.objects.visible_to(user)
        tasks = Task.objects.visible_to(user)
        status_counts = projects.values("status").annotate(total=Count("id"))
        status_labels = dict(Project.Status.choices)
        recent_logs = ActivityLog.objects.select_related("actor")
        if not user.is_admin_role:
            recent_logs = recent_logs.filter(actor=user)
        ctx.update({
            "projects_total": projects.count(),
            "tasks_total": tasks.count(),
            "projects_by_status": [{"label": status_labels.get(item["status"], item["status"]), "total": item["total"]} for item in status_counts],
            "tasks_waiting": tasks.filter(status=Task.Status.BLOCKED).count(),
            "tasks_overdue": tasks.filter(deadline__lt=today).exclude(status=Task.Status.DONE).count(),
            "recent_logs": recent_logs[:12],
        })
        if user.is_admin_role:
            ctx["top_staff"] = StaffPerformance.objects.select_related("staff").order_by("-score")[:5]
            ctx["staff_overdue"] = User.objects.filter(role=User.Role.STAFF).annotate(overdue=Count("assigned_tasks", filter=Q(assigned_tasks__deadline__lt=today) & ~Q(assigned_tasks__status=Task.Status.DONE))).order_by("-overdue")[:5]
        elif user.is_manager_role:
            staff_ids = ManagerStaffRelation.objects.filter(manager=user).values_list("staff_id", flat=True)
            ctx["staff_performance"] = StaffPerformance.objects.filter(staff_id__in=staff_ids).select_related("staff")
        return ctx


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role


class SystemMaintenanceView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = "core/system_maintenance.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        backups = list_backups()
        ctx["settings_form"] = kwargs.get("settings_form") or SystemMaintenanceForm(initial={
            "telegram_bot_token": self._setting_value("telegram_bot_token"),
            "telegram_test_chat_id": self.request.user.telegram_chat_id,
        })
        ctx["restore_form"] = kwargs.get("restore_form") or RestoreBackupForm(backups=backups)
        ctx["upload_form"] = kwargs.get("upload_form") or UploadBackupForm()
        ctx["wipe_form"] = kwargs.get("wipe_form") or WipeDataForm()
        ctx["backups"] = backups
        ctx["telegram_chats"] = kwargs.get("telegram_chats", [])
        return ctx

    def _setting_value(self, key):
        from apps.core.models import SystemSetting

        return SystemSetting.objects.filter(key=key).values_list("value", flat=True).first() or ""


class SystemMaintenanceActionView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request):
        action = request.POST.get("action")
        backups = list_backups()
        if action == "save_telegram":
            form = SystemMaintenanceForm(request.POST)
            if form.is_valid():
                self._save_setting("telegram_bot_token", form.cleaned_data["telegram_bot_token"], "Token bot Telegram")
                self._save_user_chat_id(request.user, form.cleaned_data["telegram_test_chat_id"])
                messages.success(request, "Đã lưu cấu hình Telegram.")
                return redirect("system_maintenance")
            return self._render_page(request, settings_form=form)

        if action == "test_telegram":
            form = SystemMaintenanceForm(request.POST)
            if form.is_valid():
                self._save_setting("telegram_bot_token", form.cleaned_data["telegram_bot_token"], "Token bot Telegram")
                chat_id = form.cleaned_data["telegram_test_chat_id"]
                self._save_user_chat_id(request.user, chat_id)
                ok, error = self._send_telegram_test(chat_id)
                if ok:
                    messages.success(request, "Đã gửi tin nhắn test Telegram.")
                else:
                    messages.error(request, f"Không gửi được Telegram: {error}")
                return redirect("system_maintenance")
            return self._render_page(request, settings_form=form)

        if action == "fetch_telegram_chats":
            form = SystemMaintenanceForm(request.POST)
            if form.is_valid():
                self._save_setting("telegram_bot_token", form.cleaned_data["telegram_bot_token"], "Token bot Telegram")
                self._save_user_chat_id(request.user, form.cleaned_data["telegram_test_chat_id"])
                chats, error = self._fetch_telegram_chats()
                if error:
                    messages.error(request, f"Không lấy được Chat ID: {error}")
                elif chats:
                    messages.success(request, "Đã lấy danh sách Chat ID gần đây từ Telegram.")
                else:
                    messages.error(request, "Chưa thấy chat nào. Hãy mở Telegram, nhắn /start cho bot rồi bấm lại.")
                return self._render_page(request, settings_form=form, telegram_chats=chats)
            return self._render_page(request, settings_form=form)

        if action == "create_backup":
            path = create_backup()
            messages.success(request, f"Đã tạo backup: {path.name}")
            return redirect("system_maintenance")

        if action == "upload_backup":
            form = UploadBackupForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    path = save_uploaded_backup(form.cleaned_data["backup_file"])
                    messages.success(request, f"Đã tải backup lên: {path.name}")
                    return redirect("system_maintenance")
                except Exception as exc:
                    messages.error(request, f"Không tải được backup: {exc}")
            return self._render_page(request, upload_form=form)

        if action == "restore_backup":
            form = RestoreBackupForm(request.POST, backups=backups)
            if form.is_valid():
                path = restore_backup(form.cleaned_data["backup_file"])
                messages.success(request, f"Đã restore dữ liệu từ {path.name}.")
                return redirect("dashboard")
            return self._render_page(request, restore_form=form)

        if action == "wipe_data":
            form = WipeDataForm(request.POST)
            if form.is_valid():
                create_backup(prefix="before-wipe")
                wipe_operational_data()
                messages.success(request, "Đã xóa sạch dữ liệu nghiệp vụ. Tài khoản và cấu hình vẫn được giữ lại.")
                return redirect("system_maintenance")
            return self._render_page(request, wipe_form=form)

        messages.error(request, "Thao tác không hợp lệ.")
        return redirect("system_maintenance")

    def _save_setting(self, key, value, description=""):
        from apps.core.models import SystemSetting

        SystemSetting.objects.update_or_create(key=key, defaults={"value": value.strip(), "description": description})

    def _save_user_chat_id(self, user, chat_id):
        chat_id = (chat_id or "").strip()
        if user.telegram_chat_id != chat_id:
            user.telegram_chat_id = chat_id
            user.save(update_fields=["telegram_chat_id"])

    def _render_page(self, request, settings_form=None, restore_form=None, upload_form=None, wipe_form=None, telegram_chats=None):
        backups = list_backups()
        return render(request, "core/system_maintenance.html", {
            "settings_form": settings_form or SystemMaintenanceForm(initial={
                "telegram_bot_token": self._telegram_token() or "",
                "telegram_test_chat_id": request.user.telegram_chat_id,
            }),
            "restore_form": restore_form or RestoreBackupForm(backups=backups),
            "upload_form": upload_form or UploadBackupForm(),
            "wipe_form": wipe_form or WipeDataForm(),
            "backups": backups,
            "telegram_chats": telegram_chats or [],
        })

    def _send_telegram_test(self, chat_id):
        token = self._telegram_token()
        if not token:
            return False, "Chưa có Telegram Bot Token."
        if not chat_id:
            return False, "Chưa nhập Chat ID test."
        try:
            self._telegram_api_request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                {"chat_id": chat_id, "text": "PhuLinhMedia: kết nối Telegram thành công."},
            )
            return True, ""
        except Exception as exc:
            return False, str(exc)

    def _fetch_telegram_chats(self):
        token = self._telegram_token()
        if not token:
            return [], "Chưa có Telegram Bot Token."
        try:
            payload = self._telegram_api_request(f"https://api.telegram.org/bot{token}/getUpdates")
            chats = {}
            for item in payload.get("result", []):
                message = item.get("message") or item.get("edited_message") or item.get("channel_post") or {}
                chat = message.get("chat") or {}
                chat_id = chat.get("id")
                if chat_id is None:
                    continue
                name_parts = [chat.get("first_name"), chat.get("last_name")]
                name = chat.get("title") or " ".join(part for part in name_parts if part) or chat.get("username") or "Telegram chat"
                chats[str(chat_id)] = {
                    "id": chat_id,
                    "name": name,
                    "type": chat.get("type", ""),
                    "username": chat.get("username", ""),
                    "text": message.get("text", ""),
                }
            return list(chats.values()), ""
        except Exception as exc:
            return [], str(exc)

    def _telegram_api_request(self, url, payload=None):
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urlrequest.Request(url, data=data, headers=headers)
        with urlrequest.urlopen(req, timeout=8) as response:
            body = response.read().decode("utf-8")
        result = json.loads(body)
        if not result.get("ok", True):
            raise ValueError(result.get("description", "Telegram API trả về lỗi."))
        return result

    def _telegram_token(self):
        from apps.core.models import SystemSetting

        return settings.TELEGRAM_BOT_TOKEN or SystemSetting.objects.filter(key="telegram_bot_token").values_list("value", flat=True).first()


class BackupDownloadView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, filename):
        path = backup_path(filename)
        return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)
