from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, FormView
from django.core.mail import send_mail
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
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
        form.send_verification_email()
        self.request.session['verification_code'] = form.verification_code
        messages.success(self.request, 'Код подтверждения отправлен на вашу электронную почту.')
        return super().form_valid(form)


class VerifyView(FormView):
    template_name = 'registration/verify.html'
    form_class = CustomUserCreationForm

    def post(self, request, *args, **kwargs):
        code_entered = request.POST.get('verification_code')
        if code_entered == request.session.get('verification_code'):
            # Код подтвержден, теперь сохраняем пользователя
            form = self.get_form()
            if form.is_valid():
                form.save()
                #self.send_welcome_email(user.email)
                messages.success(request, 'Регистрация завершена успешно!')
                return redirect('mailing:campaign_list')  # Перенаправляем на страницу успеха
        else:
            messages.error(request, "Неверный код подтверждения.")

        return self.form_invalid(form)

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
            return redirect('mailing:campaign_list')  # Укажите свой URL для перенаправления после редактирования профиля
        return render(request, 'users/edit_profile.html', {'form': form})

