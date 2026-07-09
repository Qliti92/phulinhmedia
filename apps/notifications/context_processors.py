def unread_notifications(request):
    if request.user.is_authenticated:
        qs = request.user.notifications.filter(is_read=False)
        return {"unread_notifications_count": qs.count(), "latest_notifications": qs[:6]}
    return {"unread_notifications_count": 0, "latest_notifications": []}
