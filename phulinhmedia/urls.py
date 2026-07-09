from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dang-nhap/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("dang-xuat/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("apps.core.urls")),
    path("tai-khoan/", include("apps.accounts.urls")),
    path("du-an/", include("apps.projects.urls")),
    path("cong-viec/", include("apps.tasks.urls")),
    path("import/", include("apps.imports.urls")),
    path("thong-bao/", include("apps.notifications.urls")),
    path("bao-cao/", include("apps.reports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
