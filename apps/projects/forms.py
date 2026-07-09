from django import forms

from apps.accounts.models import ManagerStaffRelation, User
from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["domain", "manager", "staff", "status", "progress_stage", "campaign_link", "registration_link_1", "deadline", "note"]
        widgets = {"deadline": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["progress_stage"].required = False
        if user and user.is_manager_role:
            staff_ids = ManagerStaffRelation.objects.filter(manager=user).values_list("staff_id", flat=True)
            self.fields["manager"].queryset = User.objects.filter(pk=user.pk)
            self.fields["staff"].queryset = User.objects.filter(pk__in=staff_ids)


class BulkProjectForm(forms.Form):
    project_ids = forms.CharField(widget=forms.HiddenInput)
    manager = forms.ModelChoiceField(queryset=User.objects.filter(role=User.Role.MANAGER), required=False, label="Manager")
    staff = forms.ModelChoiceField(queryset=User.objects.filter(role=User.Role.STAFF), required=False, label="Nhân viên")
    status = forms.ChoiceField(choices=[("", "Giữ nguyên")] + list(Project.Status.choices), required=False, label="Trạng thái giao việc")
    progress_stage = forms.ChoiceField(choices=[("", "Giữ nguyên")] + list(Project.ProgressStage.choices), required=False, label="Trạng thái tiến trình")
    deadline = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))


class ProjectQuickUpdateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["staff", "status", "progress_stage", "campaign_link", "registration_link_1", "deadline", "note"]
        widgets = {"deadline": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["progress_stage"].required = False
        if user and user.is_staff_role:
            self.fields.pop("staff", None)
        elif user and user.is_manager_role:
            staff_ids = ManagerStaffRelation.objects.filter(manager=user).values_list("staff_id", flat=True)
            self.fields["staff"].queryset = User.objects.filter(pk__in=staff_ids)
        elif user and user.is_admin_role:
            self.fields["staff"].queryset = User.objects.filter(role=User.Role.STAFF, is_active=True)

    def clean_staff(self):
        staff = self.cleaned_data.get("staff")
        user = getattr(self, "user", None)
        return staff
