from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import ManagerStaffRelation, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "is_active", "is_locked")
    fieldsets = DjangoUserAdmin.fieldsets + (("Thông tin PhuLinhMedia", {"fields": ("full_name", "role", "telegram_chat_id", "is_locked")}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Thông tin PhuLinhMedia", {"fields": ("email", "full_name", "role")}),)


admin.site.register(ManagerStaffRelation)
