from django.urls import path

from . import views

urlpatterns = [
    path("", views.TaskListView.as_view(), name="tasks"),
    path("tao/", views.TaskCreateView.as_view(), name="task_create"),
    path("giao-hang-loat/", views.BulkTaskAssignView.as_view(), name="task_bulk_assign"),
    path("<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path("<int:pk>/cap-nhat-nhanh/", views.TaskQuickUpdateView.as_view(), name="task_quick_update"),
    path("<int:pk>/sua/", views.TaskUpdateView.as_view(), name="task_update"),
    path("<int:pk>/cap-nhat/", views.StaffTaskUpdateView.as_view(), name="task_staff_update"),
    path("<int:pk>/duyet/", views.TaskReviewView.as_view(), name="task_review"),
]
