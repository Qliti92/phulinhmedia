from django.urls import path

from .views import BackupDownloadView, DashboardView, SystemMaintenanceActionView, SystemMaintenanceView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("he-thong/", SystemMaintenanceView.as_view(), name="system_maintenance"),
    path("he-thong/thao-tac/", SystemMaintenanceActionView.as_view(), name="system_maintenance_action"),
    path("he-thong/backup/<str:filename>/tai-ve/", BackupDownloadView.as_view(), name="backup_download"),
]
