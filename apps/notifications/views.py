from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = "notifications/notification_list.html"
    paginate_by = 30

    def get_queryset(self):
        qs = self.request.user.notifications.all()
        status = self.request.GET.get("status")
        event_type = self.request.GET.get("event_type")
        if status == "unread":
            qs = qs.filter(is_read=False)
        elif status == "read":
            qs = qs.filter(is_read=True)
        if event_type:
            qs = qs.filter(event_type=event_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["event_types"] = Notification.EventType.choices
        return ctx


class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(request.user.notifications, pk=pk)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return redirect(notification.url or "notifications")


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, "Đã đánh dấu tất cả thông báo là đã đọc.")
        return redirect("notifications")
