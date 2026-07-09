from django import forms


class SystemMaintenanceForm(forms.Form):
    telegram_bot_token = forms.CharField(
        label="Telegram Bot Token",
        required=False,
        widget=forms.PasswordInput(render_value=True),
    )
    telegram_test_chat_id = forms.CharField(
        label="Chat ID test",
        required=False,
        help_text="Nhắn /start cho bot trên Telegram, bấm Lấy Chat ID, rồi dán ID tìm được vào ô này.",
    )


class RestoreBackupForm(forms.Form):
    backup_file = forms.ChoiceField(label="File backup")
    confirm = forms.CharField(label="Nhập RESTORE để xác nhận")

    def __init__(self, *args, backups=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [(item["name"], item["name"]) for item in backups or []]
        self.fields["backup_file"].choices = choices

    def clean_confirm(self):
        value = self.cleaned_data["confirm"].strip()
        if value != "RESTORE":
            raise forms.ValidationError("Bạn cần nhập đúng RESTORE.")
        return value


class UploadBackupForm(forms.Form):
    backup_file = forms.FileField(label="Tải file backup lên")

    def clean_backup_file(self):
        file = self.cleaned_data["backup_file"]
        if not file.name.lower().endswith(".json"):
            raise forms.ValidationError("Chỉ hỗ trợ file .json.")
        return file


class WipeDataForm(forms.Form):
    confirm = forms.CharField(label="Nhập DELETE để xác nhận")

    def clean_confirm(self):
        value = self.cleaned_data["confirm"].strip()
        if value != "DELETE":
            raise forms.ValidationError("Bạn cần nhập đúng DELETE.")
        return value
