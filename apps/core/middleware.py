from .models import ActivityLog, readable_request_action


class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            friendly_action = readable_request_action(request.method, request.path)
            ActivityLog.objects.create(
                actor=request.user,
                action=friendly_action,
                object_type=request.resolver_match.view_name if request.resolver_match else "",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        return response
