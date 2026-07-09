from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.services import fetch_telegram_chats, send_telegram_message, telegram_bot_token

from .forms import AdminUserPasswordForm, ManagerStaffRelationForm, TelegramConnectionForm, UserForm, UserUpdateForm
from .models import ManagerStaffRelation, User


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    paginate_by = 20


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("users")


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("users")


class UserPasswordChangeView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "accounts/user_password_form.html"

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return self._render(request, user, AdminUserPasswordForm(user))

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = AdminUserPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Đã đổi mật khẩu cho {user.full_name or user.email}.")
            return redirect("users")
        return self._render(request, user, form)

    def _render(self, request, user, form):
        from django.shortcuts import render

        return render(request, self.template_name, {"target_user": user, "form": form})


class TelegramConnectionView(LoginRequiredMixin, View):
    template_name = "accounts/telegram_connection.html"

    def get(self, request):
        form = TelegramConnectionForm(initial={"telegram_chat_id": request.user.telegram_chat_id})
        return self._render(request, form)

    def post(self, request):
        action = request.POST.get("action")
        form = TelegramConnectionForm(request.POST)
        chats = []

        if action == "select_chat":
            chat_id = (request.POST.get("chat_id") or "").strip()
            if chat_id:
                self._save_chat_id(request.user, chat_id)
                messages.success(request, "Đã lưu Chat ID Telegram của bạn.")
            return redirect("telegram_connection")

        if form.is_valid():
            chat_id = form.cleaned_data["telegram_chat_id"].strip()
            if action in {"save", "test"}:
                self._save_chat_id(request.user, chat_id)
                if action == "save":
                    messages.success(request, "Đã lưu Chat ID Telegram của bạn.")
                    return redirect("telegram_connection")
                ok, error = send_telegram_message(chat_id, "PhuLinhMedia: kết nối Telegram của bạn đã hoạt động.")
                if ok:
                    messages.success(request, "Đã gửi tin nhắn test tới Telegram của bạn.")
                else:
                    messages.error(request, f"Không gửi được Telegram: {error}")
                return redirect("telegram_connection")
            if action == "fetch":
                chats, error = fetch_telegram_chats()
                if error:
                    messages.error(request, f"Không lấy được Chat ID: {error}")
                elif chats:
                    messages.success(request, "Đã lấy danh sách Chat ID gần đây. Chọn đúng chat của bạn để lưu.")
                else:
                    messages.error(request, "Chưa thấy chat nào. Hãy nhắn /start cho bot trên Telegram rồi bấm lại.")
        return self._render(request, form, chats)

    def _save_chat_id(self, user, chat_id):
        if user.telegram_chat_id != chat_id:
            user.telegram_chat_id = chat_id
            user.save(update_fields=["telegram_chat_id"])

    def _render(self, request, form, chats=None):
        return render(request, self.template_name, {
            "form": form,
            "telegram_chats": chats or [],
            "bot_ready": bool(telegram_bot_token()),
        })


class RelationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = ManagerStaffRelation
    template_name = "accounts/relation_list.html"


class RelationCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = ManagerStaffRelation
    form_class = ManagerStaffRelationForm
    template_name = "accounts/relation_form.html"
    success_url = reverse_lazy("relations")
