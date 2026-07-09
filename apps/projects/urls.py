from django.urls import path

from . import views

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="projects"),
    path("tao/", views.ProjectCreateView.as_view(), name="project_create"),
    path("bulk/", views.BulkProjectUpdateView.as_view(), name="project_bulk"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path("<int:pk>/cap-nhat-nhanh/", views.ProjectQuickUpdateView.as_view(), name="project_quick_update"),
    path("<int:pk>/sua/", views.ProjectUpdateView.as_view(), name="project_update"),
]
