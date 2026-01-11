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

from config.settings import DEFAULT_FROM_EMAIL
from mailing.models import Campaign, Subscriber
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, VerificationCodeForm, \
    ResetPasswordForm
from .models import CustomUser, TemporaryUser
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
        user = form.save(commit=False)  # Не сохраняем пользователя сразу
        user.save()  # Сохраняем пользователя, чтобы получить его ID

        verification_code = self.send_verification_email(user.email)

        # Создаем временного пользователя
        temporary_user = TemporaryUser.objects.create(
            user=user,
            verification_code=verification_code
        )

        self.request.session['email'] = user.email
        messages.success(self.request, 'Код подтверждения отправлен на вашу электронную почту.')
        return redirect(self.success_url)


    def send_verification_email(self, user_email):
        verification_code = str(random.randint(100000, 999999))  # Генерация 6-значного кода

        send_mail(
            'Ваш код подтверждения',
            f'Ваш код подтверждения: {verification_code}',
            DEFAULT_FROM_EMAIL,
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
                temporary_user = TemporaryUser.objects.get(
                    user__email=request.session['email']
                )

                if temporary_user.is_expired():
                    messages.error(request, "Срок действия кода подтверждения истек.")
                    return self.form_invalid(form)

                if code_entered == temporary_user.verification_code:
                    user = temporary_user.user
                    user.email_confirmed = True
                    user.save()
                    messages.success(request, 'Регистрация завершена успешно!')

                    self.send_welcome_email(user.email)

                    # Удаляем временного пользователя после успешной верификации
                    temporary_user.delete()

                    return redirect('mailing:campaign_list')
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
        context['error_message'] = messages.get_messages(self.request)
        return context

    def send_welcome_email(self, user_email):
        subject = 'Добро пожаловать в наш сервис!'
        message = 'Спасибо что зарегистрировались!'
        from_email = DEFAULT_FROM_EMAIL
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
        from_email = DEFAULT_FROM_EMAIL
        recipient_list = [user_email,]
        send_mail(subject, message, from_email, recipient_list)


class UserDetailView(View):
    def get(self, request, username):
        user = get_object_or_404(CustomUser, username=username)
        context = {
            'user': user,
            'is_manager': self.request.user.is_staff or self.request.user.groups.filter(name='Менеджер').exists(),
            'subscribers_count': Subscriber.objects.filter(owner=user).count(),
            'campaign_count': Campaign.objects.filter(owner=user).count(),
            'is_owner_profile': user.pk == self.request.user.pk
        }
        return render(request, 'users/user_detail.html', context)


class UsersListView(View):
    def get(self, request):
        users = CustomUser.objects.all()

        context = {
            'users': users,
            'users_count': users.count()
        }

        return render(request, 'users/users_list.html', context)


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
            return redirect('users:user_detail', username=user.username)  # Укажите свой URL для перенаправления после редактирования профиля
        return render(request, 'users/edit_profile.html', {'form': form})


