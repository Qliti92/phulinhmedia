from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.accounts.models import ManagerStaffRelation, User
from apps.core.services import notify_project_assigned, notify_project_updated
from .forms import ProjectForm, ProjectQuickUpdateForm
from .models import Project


class ProjectAccessMixin(LoginRequiredMixin):
    def get_queryset(self):
        return Project.objects.select_related("manager", "staff").visible_to(self.request.user)


class CanManageProjectMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin_role or self.request.user.is_manager_role


class ProjectListView(ProjectAccessMixin, ListView):
    template_name = "projects/project_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        status = self.request.GET.get("status")
        progress_stage = self.request.GET.get("progress_stage")
        staff = self.request.GET.get("staff")
        if q:
            qs = qs.filter(domain__icontains=q)
        if status:
            qs = qs.filter(status=status)
        if progress_stage:
            qs = qs.filter(progress_stage=progress_stage)
        if staff:
            qs = qs.filter(staff_id=staff)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Project.Status.choices
        ctx["progress_stages"] = Project.ProgressStage.choices
        ctx["can_manage_projects"] = self.request.user.is_admin_role or self.request.user.is_manager_role
        if self.request.user.is_manager_role:
            staff_ids = ManagerStaffRelation.objects.filter(manager=self.request.user).values_list("staff_id", flat=True)
            ctx["staff_options"] = User.objects.filter(pk__in=staff_ids).select_related("manager_relation")
        elif self.request.user.is_admin_role:
            ctx["staff_options"] = User.objects.filter(role=User.Role.STAFF, is_active=True).select_related("manager_relation")
            ctx["manager_options"] = User.objects.filter(role=User.Role.MANAGER, is_active=True)
        else:
            ctx["staff_options"] = User.objects.none()
            ctx["manager_options"] = User.objects.none()
        return ctx


class ProjectCreateView(ProjectAccessMixin, CanManageProjectMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_url = reverse_lazy("projects")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        notify_project_assigned(self.object, actor=self.request.user)
        return response


class ProjectUpdateView(ProjectAccessMixin, CanManageProjectMixin, UpdateView):
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_url = reverse_lazy("projects")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        notify_project_updated(self.object, actor=self.request.user)
        return response


class ProjectDetailView(ProjectAccessMixin, DetailView):
    template_name = "projects/project_detail.html"


class BulkProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_admin_role or self.request.user.is_manager_role

    def post(self, request):
        ids = [int(pk) for pk in request.POST.get("project_ids", "").split(",") if pk.strip().isdigit()]
        if not ids:
            messages.error(request, "Vui lòng chọn ít nhất một dự án.")
            return redirect("projects")

        projects = Project.objects.visible_to(request.user).filter(pk__in=ids)
        manager_id = request.POST.get("manager")
        if request.user.is_manager_role:
            staff_ids = set(ManagerStaffRelation.objects.filter(manager=request.user).values_list("staff_id", flat=True))
        elif manager_id:
            staff_ids = set(ManagerStaffRelation.objects.filter(manager_id=manager_id).values_list("staff_id", flat=True))
        else:
            staff_ids = set(User.objects.filter(role=User.Role.STAFF).values_list("id", flat=True))

        staff_id = request.POST.get("staff")
        status = request.POST.get("status")
        progress_stage = request.POST.get("progress_stage")
        deadline = request.POST.get("deadline")

        count = 0
        for project in projects:
            if request.user.is_manager_role:
                project.manager = request.user
            elif manager_id:
                project.manager_id = manager_id
            if staff_id:
                selected_staff_id = int(staff_id)
                if selected_staff_id in staff_ids:
                    project.staff_id = selected_staff_id
            if status:
                project.status = status
            if progress_stage:
                project.progress_stage = progress_stage
            if deadline:
                project.deadline = deadline
            project.save()
            notify_project_assigned(project, actor=request.user)
            count += 1

        messages.success(request, f"Đã giao việc/cập nhật hàng loạt {count} dự án.")
        return redirect("projects")


class ProjectQuickUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project.objects.visible_to(request.user), pk=pk)
        form = ProjectQuickUpdateForm(request.POST, instance=project, user=request.user)
        if form.is_valid():
            item = form.save(commit=False)
            if request.user.is_manager_role:
                item.manager = request.user
            item.save()
            notify_project_updated(item, actor=request.user)
            messages.success(request, "Đã cập nhật dự án.")
        else:
            messages.error(request, "Không thể cập nhật dự án. Vui lòng kiểm tra lại dữ liệu.")
        return redirect("projects")
