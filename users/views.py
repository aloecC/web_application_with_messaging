import random

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.http import request

from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.core.mail import send_mail
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, VerificationCodeForm, \
    ResetPasswordForm
from .models import CustomUser
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.contrib import messages


class RegisterView(FormView):
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:verify')

    def form_valid(self, form):
        user = form.save()
        verification_code = self.send_verification_email(user.email)
        user.verification_code = verification_code
        user.save()
        self.request.session['email'] = user.email
        messages.success(self.request, 'Код подтверждения отправлен на вашу электронную почту.')
        return redirect(self.success_url)

    def send_verification_email(self, user_email):
        verification_code = str(random.randint(100000, 999999))  # Генерация 6-значного кода

        send_mail(
            'Ваш код подтверждения',
            f'Ваш код подтверждения: {verification_code}',
            'daryaaloets@yandex.ru',
            [user_email],
            fail_silently=False,
        )

        return verification_code


class VerifyView(FormView):
    template_name = 'users/verify.html'
    user = CustomUser
    form_class = VerificationCodeForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            code_entered = form.cleaned_data['verification_code']
            try:
                user = CustomUser.objects.get(
                    email=request.session['email'])
                if code_entered == user.verification_code:
                    user.email_confirmed = True
                    user.save()
                    messages.success(request, 'Регистрация завершена успешно!')

                    self.send_welcome_email(user.email)
                    return redirect('mailing:campaign_list')
                else:
                    messages.error(request, "Неверный код подтверждения.")
            except CustomUser.DoesNotExist:
                messages.error(request, "Пользователь не найден.")

        return self.form_invalid(form)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['error_message'] = messages.get_messages(self.request)
        return context


    def send_welcome_email(self, user_email):
        subject = 'Добро пожаловать в наш сервис!'
        message = 'Спасибо что зарегистрировались!'
        from_email = 'daryaaloets@yandex.ru'
        recipient_list = [user_email,]
        send_mail(subject, message, from_email, recipient_list)


class LoginView(View):

    def get(self, request, *args, **kwargs):
        return render(request, 'login.html')

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Логика аутентификации пользователя
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            print(f"Отправка письма на: {user.email}")
            self.send_login_email(user.email)
            return redirect('home')
        else:
            # Обработка ошибки аутентификации
            return render(request, 'login.html', {'error': 'Неверные учетные данные'})

    def send_login_email(self, user_email):
        subject = 'Произведена попытка входа'
        message = 'Если это не вы - смените пароль по ссылке ниже'
        from_email = 'daryaaloets@yandex.ru'
        recipient_list = [user_email,]
        send_mail(subject, message, from_email, recipient_list)


class UserDetailView(View):
    def get(self, request, username):
        user = get_object_or_404(CustomUser, username=username)
        return render(request, 'users/user_detail.html', {'user': user})


class UserProfileEditView(LoginRequiredMixin, View):
    def get(self, request, username):
        user = get_object_or_404(CustomUser, username=username)
        form = UserProfileForm(instance=request.user)
        return render(request, 'users/edit_profile.html', {'form': form})

    def post(self, request, username):
        user = get_object_or_404(CustomUser, username=username)
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('users:user_detail')  # Укажите свой URL для перенаправления после редактирования профиля
        return render(request, 'users/edit_profile.html', {'form': form})


class PasswordResetView(View):
    template_name = 'users/password_reset_form.html '
    form_class = ResetPasswordForm
    user = CustomUser
    success_url = reverse_lazy('users:password_reset_done')

    def form_valid(self, form):
        user = form.save()
        self.send_password_reset_email(user)
        self.request.session['email'] = user.email
        messages.success(self.request, 'Ссылка для сброса пароля отправлена на вашу электронную почту.')
        return redirect(self.success_url)

    def send_password_reset_email(self, user):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk)).decode()
        domain = self.request.get_host()
        reset_link = f'http://{domain}{reverse("users:password_reset_confirm", kwargs={"uidb64": uid, "token": token})}'

        send_mail(
            'Сброс пароля',
            f'Перейдите по следующей ссылке, чтобы сбросить пароль: {reset_link}',
            'daryaaloets@yandex.ru',
            [user.email],
            fail_silently=False,
        )


class PasswordResetDoneView(View):
    template_name = 'users/password_reset_done.html'
    form_class = ResetPasswordForm
    user = CustomUser
    success_url = reverse_lazy('users:password_reset_confirm')


class PasswordResetConfirmView(View):
    template_name = 'users/password_reset_confirm.html'
    form_class = ResetPasswordForm
    user = CustomUser
    success_url = reverse_lazy('users:password_reset_complete')

    def form_valid(self):
        return redirect(self.success_url)


class PasswordResetCompleteView(View):
    template_name = 'users/password_reset_complete.html'
    form_class = ResetPasswordForm
    user = CustomUser
    success_url = reverse_lazy('users:login')

