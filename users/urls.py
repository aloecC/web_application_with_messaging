from django.urls import path
from . import views
from .forms import CustomAuthenticationForm
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, \
    PasswordResetConfirmView, PasswordResetCompleteView

from .views import RegisterView, UserDetailView, UserProfileEditView, VerifyView

#Пространство имен(помогает избежать ошибки при одинаковых именах маршрута)
app_name = 'users'

#В urlpatterns создаются и регестрируются маршруты
#Path это специальная функция которая позволяет регестрировать наш маршрут
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', VerifyView.as_view(), name='verify'),
    path('login/', LoginView.as_view(template_name='users/login.html', form_class=CustomAuthenticationForm), name='login'),
    path('logout/', LogoutView.as_view(next_page='mailing:campaign_list'), name='logout'),
    path('profile/<str:username>/', UserDetailView.as_view(), name='user_detail'),
    path('profile/edit/<str:username>/', UserProfileEditView.as_view(), name='edit_profile'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

# password_reset_form.html — форма для ввода электронной почты.
# password_reset_done.html — сообщение о том, что письмо с инструкциями отправлено.
# password_reset_confirm.html — форма для ввода нового пароля.
# password_reset_complete.html — сообщение о том, что пароль успешно изменен.