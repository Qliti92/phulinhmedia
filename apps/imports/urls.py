from django.urls import path

from . import views

urlpatterns = [
    path("", views.ImportListView.as_view(), name="imports"),
    path("tai-len/", views.ImportCreateView.as_view(), name="import_create"),
    path("<int:pk>/", views.ImportDetailView.as_view(), name="import_detail"),
    path("<int:pk>/luu/", views.ImportCommitView.as_view(), name="import_commit"),
    path("<int:pk>/bao-cao/", views.ImportReportView.as_view(), name="import_report"),
]
