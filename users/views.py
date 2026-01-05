from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView
from django.views.generic.edit import CreateView
from django.core.mail import send_mail
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .models import CustomUser


class RegisterView(CreateView):
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('mailing:campaign_list')

    def form_valid(self, form):
        user = form.save()
        self.send_welcome_email(user.email)
        return super().form_valid(form)

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

