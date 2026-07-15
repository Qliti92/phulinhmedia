from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.accounts.models import ManagerStaffRelation, User
from apps.core.services import notify_task_assigned, notify_task_reviewed, notify_task_updated
from .forms import BulkTaskAssignForm, ReviewTaskForm, StaffTaskUpdateForm, TaskAttachmentForm, TaskForm, TaskQuickUpdateForm
from .models import Task


class TaskAccessMixin(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.select_related("assignee", "created_by").visible_to(self.request.user)


class CanAssignTaskMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin_role or self.request.user.is_manager_role


class TaskListView(TaskAccessMixin, ListView):
    template_name = "tasks/task_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get("status")
        q = self.request.GET.get("q")
        assignee = self.request.GET.get("assignee")
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(title__icontains=q)
        if assignee:
            qs = qs.filter(assignee_id=assignee)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Task.Status.choices
        if self.request.user.is_admin_role or self.request.user.is_manager_role:
            ctx["bulk_form"] = BulkTaskAssignForm(user=self.request.user)
            if self.request.user.is_admin_role:
                ctx["assignee_options"] = User.objects.filter(role__in=[User.Role.MANAGER, User.Role.STAFF], is_active=True)
            else:
                staff_ids = ManagerStaffRelation.objects.filter(manager=self.request.user).values_list("staff_id", flat=True)
                ctx["assignee_options"] = User.objects.filter(pk__in=staff_ids, is_active=True)
        return ctx


class TaskCreateView(TaskAccessMixin, CanAssignTaskMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"
    success_url = reverse_lazy("tasks")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        if self.object.assignee:
            notify_task_assigned(self.object, actor=self.request.user)
        return response


class TaskUpdateView(TaskAccessMixin, CanAssignTaskMixin, UpdateView):
    form_class = TaskForm
    template_name = "tasks/task_form.html"
    success_url = reverse_lazy("tasks")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        notify_task_updated(self.object, actor=self.request.user)
        return response


class BulkTaskAssignView(TaskAccessMixin, CanAssignTaskMixin, View):
    def post(self, request):
        form = BulkTaskAssignForm(request.POST, user=request.user)
        if form.is_valid():
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            deadline = form.cleaned_data["deadline"]
            assignees = form.cleaned_data["assignees"]
            tasks = [
                Task(
                    title=title,
                    description=description,
                    deadline=deadline,
                    assignee=assignee,
                    created_by=request.user,
                    status=Task.Status.ASSIGNED,
                )
                for assignee in assignees
            ]
            created_tasks = Task.objects.bulk_create(tasks)
            for task in created_tasks:
                notify_task_assigned(task, actor=request.user)
            messages.success(request, f"Đã giao hàng loạt {len(tasks)} công việc.")
        else:
            messages.error(request, "Không thể giao hàng loạt. Vui lòng kiểm tra lại.")
        return redirect("tasks")


class TaskQuickUpdateView(TaskAccessMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task.objects.visible_to(request.user), pk=pk)
        form = TaskQuickUpdateForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            notify_task_updated(task, actor=request.user)
            messages.success(request, "Đã cập nhật công việc.")
        else:
            messages.error(request, "Không thể cập nhật công việc. Vui lòng kiểm tra lại.")
        return redirect("tasks")


class StaffTaskUpdateView(TaskAccessMixin, UpdateView):
    form_class = StaffTaskUpdateForm
    template_name = "tasks/task_staff_update.html"
    success_url = reverse_lazy("tasks")

    def get_queryset(self):
        return super().get_queryset().filter(assignee=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        notify_task_updated(self.object, actor=self.request.user)
        return response


class TaskReviewView(TaskAccessMixin, CanAssignTaskMixin, UpdateView):
    form_class = ReviewTaskForm
    template_name = "tasks/task_review.html"
    success_url = reverse_lazy("tasks")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.assignee:
            notify_task_reviewed(self.object, actor=self.request.user)
        return response


class TaskDetailView(TaskAccessMixin, DetailView):
    template_name = "tasks/task_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["attachment_form"] = TaskAttachmentForm()
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = TaskAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.task = self.object
            attachment.uploaded_by = request.user
            attachment.save()
            messages.success(request, "Đã tải file minh chứng.")
        return redirect("task_detail", pk=self.object.pk)
