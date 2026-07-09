from django.contrib import admin

from .models import Attendance, StaffPerformance, Task, TaskAttachment

admin.site.register(Task)
admin.site.register(TaskAttachment)
admin.site.register(StaffPerformance)
admin.site.register(Attendance)
