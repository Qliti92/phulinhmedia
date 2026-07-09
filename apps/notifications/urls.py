from django.urls import path

from . import views

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notifications"),
    path("da-doc-tat-ca/", views.MarkAllNotificationsReadView.as_view(), name="notifications_mark_all_read"),
    path("<int:pk>/da-doc/", views.MarkNotificationReadView.as_view(), name="notification_mark_read"),
]
