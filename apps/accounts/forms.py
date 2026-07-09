from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm

from .models import ManagerStaffRelation, User


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["email", "full_name", "role", "telegram_chat_id", "is_active", "is_locked"]


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "full_name", "role", "telegram_chat_id", "is_active", "is_locked"]


class AdminUserPasswordForm(SetPasswordForm):
    pass


class TelegramConnectionForm(forms.Form):
    telegram_chat_id = forms.CharField(
        label="Telegram Chat ID của bạn",
        required=False,
        help_text="Nhắn /start cho bot, bấm Lấy Chat ID, rồi chọn hoặc nhập ID của bạn.",
    )


class ManagerStaffRelationForm(forms.ModelForm):
    class Meta:
        model = ManagerStaffRelation
        fields = ["manager", "staff"]
