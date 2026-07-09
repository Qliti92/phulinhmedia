import json
from urllib import request as urlrequest

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import ManagerStaffRelation, User
from apps.core.models import SystemSetting
from apps.notifications.models import Notification


NOTIFICATION_RULES = {
    "task_assigned": "Người được giao nhận thông báo; nếu người nhận là staff thì manager trực tiếp cũng nhận.",
    "task_updated": "Cập nhật của staff gửi về manager trực tiếp, không gửi vòng lên admin.",
    "task_blocked": "Vướng mắc của staff gửi về manager trực tiếp với mức quan trọng.",
    "task_done": "Hoàn thành của staff gửi về manager trực tiếp với mức quan trọng.",
    "project_assigned": "Manager và staff được gán vào dự án đều nhận thông báo.",
    "task_reviewed": "Người thực hiện nhận kết quả duyệt.",
    "deadline": "Người phụ trách nhận nhắc hạn; quá hạn được ưu tiên cao và sẵn sàng gửi Telegram.",
}


def notify_user(user, title, message, url="", event_type=Notification.EventType.SYSTEM, priority=Notification.Priority.NORMAL, channel=Notification.Channel.IN_APP):
    if not user:
        return None
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        url=url,
        event_type=event_type,
        priority=priority,
        channel=channel,
    )
    if channel in {Notification.Channel.TELEGRAM, Notification.Channel.BOTH}:
        send_telegram_notification(notification)
    return notification


def notify_many(users, title, message, url="", event_type=Notification.EventType.SYSTEM, priority=Notification.Priority.NORMAL, channel=Notification.Channel.IN_APP):
    sent = []
    seen = set()
    for user in users:
        if not user or user.pk in seen:
            continue
        seen.add(user.pk)
        notification = notify_user(user, title, message, url, event_type, priority, channel)
        if notification:
            sent.append(notification)
    return sent


def send_telegram_notification(notification):
    token = settings.TELEGRAM_BOT_TOKEN or SystemSetting.objects.filter(key="telegram_bot_token").values_list("value", flat=True).first()
    if not notification.user.telegram_chat_id:
        notification.telegram_error = "Người dùng chưa có Telegram Chat ID."
        notification.save(update_fields=["telegram_error"])
        return False
    if not token:
        notification.telegram_error = "Chưa cấu hình Telegram bot token."
        notification.save(update_fields=["telegram_error"])
        return False
    try:
        telegram_api_request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            {"chat_id": notification.user.telegram_chat_id, "text": f"{notification.title}\n{notification.message}"},
        )
        notification.telegram_sent_at = timezone.now()
        notification.telegram_error = ""
        notification.save(update_fields=["telegram_sent_at", "telegram_error"])
        return True
    except Exception as exc:
        notification.telegram_error = str(exc)
        notification.save(update_fields=["telegram_error"])
        return False


def telegram_api_request(url, payload=None):
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


def telegram_bot_token():
    return settings.TELEGRAM_BOT_TOKEN or SystemSetting.objects.filter(key="telegram_bot_token").values_list("value", flat=True).first()


def fetch_telegram_chats():
    token = telegram_bot_token()
    if not token:
        return [], "Admin chưa cấu hình Telegram Bot Token."
    try:
        payload = telegram_api_request(f"https://api.telegram.org/bot{token}/getUpdates")
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


def send_telegram_message(chat_id, text):
    token = telegram_bot_token()
    if not token:
        return False, "Admin chưa cấu hình Telegram Bot Token."
    if not chat_id:
        return False, "Chưa có Chat ID."
    try:
        telegram_api_request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            {"chat_id": chat_id, "text": text},
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)


def direct_manager_for_staff(user):
    if not user or not user.is_staff_role:
        return None
    relation = ManagerStaffRelation.objects.filter(staff=user).select_related("manager").first()
    return relation.manager if relation else None


def user_name(user):
    if not user:
        return "Hệ thống"
    return user.full_name or user.email


def task_recipients(task, event):
    recipients = []
    creator = task.created_by
    assignee = task.assignee
    if event == "assigned":
        recipients.append(assignee)
        recipients.append(direct_manager_for_staff(assignee))
    elif event in {"updated", "blocked", "done"}:
        if assignee and assignee.is_staff_role:
            recipients.append(direct_manager_for_staff(assignee))
        if assignee and assignee.is_manager_role:
            recipients.append(creator)
    elif event == "reviewed":
        recipients.append(assignee)
    return recipients


def notify_task_assigned(task, actor=None):
    actor_name = user_name(actor or task.created_by)
    assignee_name = user_name(task.assignee)
    return notify_many(
        task_recipients(task, "assigned"),
        "Giao công việc mới",
        f"{actor_name} giao công việc \"{task.title}\" cho {assignee_name}.",
        url=f"/cong-viec/{task.pk}/",
        event_type=Notification.EventType.TASK_ASSIGNED,
        priority=Notification.Priority.HIGH,
        channel=Notification.Channel.BOTH,
    )


def notify_task_updated(task, actor=None):
    actor_name = user_name(actor or task.assignee or task.created_by)
    if task.status == task.Status.BLOCKED:
        title = "Công việc có vướng mắc"
        message = f"{actor_name} báo vướng mắc trong công việc \"{task.title}\" - tiến độ {task.progress}%."
        event_type = Notification.EventType.TASK_BLOCKED
        priority = Notification.Priority.HIGH
    elif task.status == task.Status.DONE:
        title = "Hoàn thành công việc"
        message = f"{actor_name} hoàn thành công việc \"{task.title}\" - tiến độ {task.progress}%."
        event_type = Notification.EventType.TASK_DONE
        priority = Notification.Priority.HIGH
    else:
        title = "Cập nhật công việc"
        message = f"{actor_name} cập nhật công việc \"{task.title}\" lên {task.progress}%."
        event_type = Notification.EventType.TASK_UPDATED
        priority = Notification.Priority.NORMAL
    return notify_many(
        task_recipients(task, "updated" if event_type == Notification.EventType.TASK_UPDATED else task.status),
        title,
        message,
        url=f"/cong-viec/{task.pk}/",
        event_type=event_type,
        priority=priority,
        channel=Notification.Channel.BOTH if priority == Notification.Priority.HIGH else Notification.Channel.IN_APP,
    )


def notify_task_reviewed(task, actor=None):
    actor_name = user_name(actor)
    return notify_user(
        task.assignee,
        "Kết quả duyệt công việc",
        f"{actor_name} duyệt công việc \"{task.title}\": {task.get_status_display()}.",
        url=f"/cong-viec/{task.pk}/",
        event_type=Notification.EventType.TASK_REVIEWED,
        priority=Notification.Priority.NORMAL,
    )


def project_assignment_recipients(project):
    return [project.manager, project.staff]


def project_update_recipients(project, actor=None):
    if actor and actor.is_staff_role:
        return [project.manager or direct_manager_for_staff(actor)]
    if actor and actor.is_manager_role:
        return [project.staff]
    return project_assignment_recipients(project)


def notify_project_assigned(project, actor=None):
    actor_name = user_name(actor or project.created_by)
    participants = ", ".join([user_name(user) for user in project_assignment_recipients(project) if user])
    return notify_many(
        project_assignment_recipients(project),
        "Giao dự án",
        f"{actor_name} gán dự án \"{project.domain}\" cho {participants or 'người phụ trách'}.",
        url=f"/du-an/{project.pk}/",
        event_type=Notification.EventType.PROJECT_ASSIGNED,
        priority=Notification.Priority.HIGH,
        channel=Notification.Channel.BOTH,
    )


def notify_project_updated(project, actor=None):
    actor_name = user_name(actor)
    return notify_many(
        project_update_recipients(project, actor),
        "Cập nhật dự án",
        f"{actor_name} cập nhật tiến trình dự án \"{project.domain}\" lên {project.progress}%.",
        url=f"/du-an/{project.pk}/",
        event_type=Notification.EventType.PROJECT_UPDATED,
        priority=Notification.Priority.NORMAL,
        channel=Notification.Channel.IN_APP,
    )
