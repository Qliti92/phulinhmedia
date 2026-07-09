from django.urls import path

from . import views

urlpatterns = [
    path("", views.ReportDashboardView.as_view(), name="reports"),
    path("xep-hang/hien-thi/", views.RankingVisibilityView.as_view(), name="ranking_visibility"),
    path("du-an.xlsx", views.ProjectExcelView.as_view(), name="export_projects"),
    path("cong-viec.xlsx", views.TaskExcelView.as_view(), name="export_tasks"),
    path("hieu-suat.xlsx", views.PerformanceExcelView.as_view(), name="export_performance"),
    path("log.xlsx", views.LogsExcelView.as_view(), name="export_logs"),
    path("tong-hop.pdf", views.SummaryPdfView.as_view(), name="export_pdf"),
]
