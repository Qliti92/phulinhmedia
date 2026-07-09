from django.urls import path

from . import views

urlpatterns = [
    path("", views.UserListView.as_view(), name="users"),
    path("telegram/", views.TelegramConnectionView.as_view(), name="telegram_connection"),
    path("tao/", views.UserCreateView.as_view(), name="user_create"),
    path("<int:pk>/sua/", views.UserUpdateView.as_view(), name="user_update"),
    path("<int:pk>/doi-mat-khau/", views.UserPasswordChangeView.as_view(), name="user_password_change"),
    path("phan-cong/", views.RelationListView.as_view(), name="relations"),
    path("phan-cong/tao/", views.RelationCreateView.as_view(), name="relation_create"),
]
