from django import forms

from apps.accounts.models import ManagerStaffRelation, User
from .models import Task, TaskAttachment


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "assignee", "status", "progress", "blocker_note", "deadline"]
        widgets = {"deadline": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_admin_role:
            self.fields["assignee"].queryset = User.objects.filter(role__in=[User.Role.MANAGER, User.Role.STAFF], is_active=True)
        elif user and user.is_manager_role:
            staff_ids = ManagerStaffRelation.objects.filter(manager=user).values_list("staff_id", flat=True)
            self.fields["assignee"].queryset = User.objects.filter(pk__in=staff_ids, is_active=True)


class BulkTaskAssignForm(forms.Form):
    title = forms.CharField(label="Tên công việc", max_length=220)
    assignees = forms.ModelMultipleChoiceField(label="Người nhận", queryset=User.objects.none())
    description = forms.CharField(label="Mô tả", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    deadline = forms.DateField(label="Deadline", required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_admin_role:
            self.fields["assignees"].queryset = User.objects.filter(role__in=[User.Role.MANAGER, User.Role.STAFF], is_active=True)
        elif user and user.is_manager_role:
            staff_ids = ManagerStaffRelation.objects.filter(manager=user).values_list("staff_id", flat=True)
            self.fields["assignees"].queryset = User.objects.filter(pk__in=staff_ids, is_active=True)


class TaskQuickUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["status", "progress", "blocker_note", "completion_note", "deadline"]
        widgets = {"deadline": forms.DateInput(attrs={"type": "date"})}


class StaffTaskUpdateForm(TaskQuickUpdateForm):
    pass


class ReviewTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["status", "progress", "completion_note"]


class TaskAttachmentForm(forms.ModelForm):
    class Meta:
        model = TaskAttachment
        fields = ["file", "note"]
