from django.contrib import admin

from .models import ActivityLog, SystemSetting

admin.site.register(ActivityLog)
admin.site.register(SystemSetting)
