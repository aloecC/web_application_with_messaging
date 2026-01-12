import random

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.core.mail import send_mail
from django.http import request
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView

from config.settings import DEFAULT_FROM_EMAIL, EMAIL_HOST_USER
from mailing.models import Campaign, Subscriber

from .forms import (
    CustomAuthenticationForm,
    CustomUserCreationForm,
    ResetPasswordForm,
    UserPasswordChangeForm,
    UserProfileForm,
    VerificationCodeForm,
)
from .models import CustomUser, TemporaryUser


class RegisterView(FormView):
    template_name = "users/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("users:verify")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password1"]
        username = form.cleaned_data["username"]

        verification_code = self.send_verification_email(email)

        # Создаем временного пользователя
        temporary_user = TemporaryUser.objects.create(
            email=email,
            verification_code=verification_code,
            password=password,
            username=username,
        )

        self.request.session["email"] = email
        messages.success(self.request, "Код подтверждения отправлен на вашу электронную почту.")
        return redirect(self.success_url)

    def send_verification_email(self, user_email):
        verification_code = str(random.randint(100000, 999999))  # Генерация 6-значного кода

        send_mail(
            "Ваш код подтверждения",
            f"Ваш код подтверждения: {verification_code}",
            DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )

        return verification_code


class VerifyView(FormView):
    template_name = "users/verify.html"
    form_class = VerificationCodeForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            code_entered = form.cleaned_data["verification_code"]
            try:
                temporary_user = TemporaryUser.objects.get(email=request.session["email"])

                if temporary_user.is_expired():
                    messages.error(request, "Срок действия кода подтверждения истек.")
                    temporary_user.delete()
                    return self.form_invalid(form)

                if code_entered == temporary_user.verification_code:
                    user = CustomUser.objects.create(
                        email=temporary_user.email,
                        username=temporary_user.username,
                        password=temporary_user.password,
                        email_confirmed=True,
                    )
                    user.set_password(temporary_user.password)
                    user.save()

                    messages.success(request, "Регистрация завершена успешно!")

                    self.send_welcome_email(user.email)

                    # Удаляем временного пользователя после успешной верификации
                    temporary_user.delete()

                    return redirect("mailing:campaign_list")
                else:
                    messages.error(request, "Неверный код подтверждения.")
            except TemporaryUser.DoesNotExist:
                messages.error(request, "Пользователь не найден.")

            return self.form_invalid(form)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["error_message"] = messages.get_messages(self.request)
        return context

    def send_welcome_email(self, user_email):
        subject = "Добро пожаловать в наш сервис!"
        message = "Спасибо что зарегистрировались!"
        from_email = DEFAULT_FROM_EMAIL
        recipient_list = [
            user_email,
        ]
        send_mail(subject, message, from_email, recipient_list)


class LoginView(View):
    """Вход в систему"""

    def get(self, request, *args, **kwargs):
        return render(request, "login.html")

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Логика аутентификации пользователя
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_block:
                return render(request, "login.html", {"error": "Данный пользователь заблокирован"})
            else:
                login(request, user)
                print(f"Отправка письма на: {user.email}")
                self.send_login_email(user.email)
                return redirect("home")
        else:
            # Обработка ошибки аутентификации
            return render(request, "login.html", {"error": "Неверные учетные данные"})

    def send_login_email(self, user_email):
        subject = "Произведена попытка входа"
        message = "Если это не вы - смените пароль по ссылке ниже"
        from_email = DEFAULT_FROM_EMAIL
        recipient_list = [
            user_email,
        ]
        send_mail(subject, message, from_email, recipient_list)


class UserDetailView(View):
    def get(self, request, username):
        user = get_object_or_404(CustomUser, username=username)
        is_block = ""
        if user.is_block:
            is_block = "Заблокирован"
        else:
            is_block = "Не заблокирован"

        context = {
            "user": user,
            "is_manager": self.request.user.groups.filter(name="Менеджер").exists(),
            "subscribers_count": Subscriber.objects.filter(owner=user).count(),
            "campaign_count": Campaign.objects.filter(owner=user).count(),
            "is_owner_profile": user.pk == self.request.user.pk,
            "is_block": is_block,
        }
        return render(request, "users/user_detail.html", context)


class UserProfileView(View):
    """Личный профиль"""

    def get(self, request):
        user = self.request.user
        is_block = ""
        if user.is_block:
            is_block = "Заблокирован"
        else:
            is_block = "Не заблокирован"

        context = {
            "user": user,
            "is_manager": self.request.user.groups.filter(name="Менеджер").exists(),
            "subscribers_count": Subscriber.objects.filter(owner=user).count(),
            "campaign_count": Campaign.objects.filter(owner=user).count(),
            "is_block": is_block,
        }
        return render(request, "users/user_profile.html", context)


class UsersListView(View):
    def get(self, request):
        users = CustomUser.objects.all()

        context = {"users": users, "users_count": users.count()}

        return render(request, "users/users_list.html", context)


@method_decorator(cache_page(60 * 15), name="dispatch")
class UserProfileEditView(LoginRequiredMixin, View):
    """Редактирование профиля пользователя"""

    def get(self, request):
        form = UserProfileForm(instance=request.user)
        return render(request, "users/edit_profile.html", {"form": form})

    def post(self, request):
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            form.save()
            return redirect("users:user_profile")  # Укажите свой URL для перенаправления после редактирования профиля
        return render(request, "users/edit_profile.html", {"form": form})


class UserBlockView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Блокировка пользователя"""

    def post(self, request, username):
        user = get_object_or_404(CustomUser, username=username)

        user.is_block = True
        user.is_active = False
        user.save()

        send_mail(
            subject="Блокировка",
            message=f"{user.username}, спешу сообщить, что вы были заблокированы. ",
            from_email=f"{EMAIL_HOST_USER}",
            recipient_list=[user.email],
        )

        return redirect("users:user_detail", username=username)

    def test_func(self):
        if self.request.user.groups.filter(name="Менеджер").exists():
            return True


class UserEndBlockView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Снятие блокировки c пользователя"""

    def post(self, request, username):
        user = get_object_or_404(CustomUser, username=username)

        user.is_block = False
        user.is_active = True
        user.save()

        send_mail(
            subject="Снятие блокировки",
            message=f"{user.username}, спешу сообщить, что вы снова можете пользоваться нашем сервисом.",
            from_email=f"{EMAIL_HOST_USER}",
            recipient_list=[user.email],
        )

        return redirect("users:user_detail", username=username)

    def test_func(self):
        if self.request.user.groups.filter(name="Менеджер").exists():
            return True


class DeleteProfileView(LoginRequiredMixin, View):
    """Представление для удаления профиля пользователя"""

    def get(self, request, username):
        """Показать страницу подтверждения удаления"""
        user = get_object_or_404(CustomUser, username=username)
        return render(request, "users/delete_profile.html", {"user": user})

    def post(self, request, username):
        """Удалить профиль пользователя"""
        user = get_object_or_404(CustomUser, username=username)
        user.delete()
        messages.success(request, "Ваш профиль был успешно удален.")
        return redirect("mailing:home")  # Перенаправление на главную страницу или другую страницу


class UserPasswordChange(PasswordChangeView):
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("users:password_change_done")
    template_name = "users/password_change_form.html"
