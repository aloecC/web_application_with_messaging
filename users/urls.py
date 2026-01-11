from django.urls import path, reverse_lazy

from .forms import CustomAuthenticationForm

from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, \
    PasswordResetConfirmView, PasswordResetCompleteView

from .views import RegisterView, UserDetailView, UserProfileEditView, VerifyView, UsersListView, UserBlockView, \
    UserEndBlockView, DeleteProfileView

#Пространство имен(помогает избежать ошибки при одинаковых именах маршрута)
app_name = 'users'

#В urlpatterns создаются и регестрируются маршруты
#Path это специальная функция которая позволяет регестрировать наш маршрут
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', VerifyView.as_view(), name='verify'),
    path('login/', LoginView.as_view(template_name='users/login.html', form_class=CustomAuthenticationForm), name='login'),
    path('logout/', LogoutView.as_view(next_page='mailing:campaign_list'), name='logout'),
    path('users/', UsersListView.as_view(), name='user_list'),

    path('profile/<str:username>/', UserDetailView.as_view(), name='user_detail'),
    path('profile/edit/<str:username>/', UserProfileEditView.as_view(), name='edit_profile'),

    path('profile/block/<str:username>/', UserBlockView.as_view(), name='user_block'),
    path('profile/endblock/<str:username>/', UserEndBlockView.as_view(), name='user_end_block'),

    path('profile/delete/<str:username>/', DeleteProfileView.as_view(), name='delete_profile'),

    #path('password-change/', views.UserPasswordChange.as_view(), name="password_change"),
    #path('password-change/done/', PasswordChangeDoneView.as_view(template_name="users/password_change_done.html"),
         #name="password_change_done"),

    path('password-reset/',
         PasswordResetView.as_view(
             template_name="users/password_reset_form.html",
             email_template_name="users/password_reset_email.html",
             success_url=reverse_lazy("users:password_reset_done")
         ),
         name='password_reset'),
    path('password-reset/done/',
         PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(
             template_name="users/password_reset_confirm.html",
             success_url=reverse_lazy("users:password_reset_complete")
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"),
         name='password_reset_complete'),

]

# password_reset_form.html — форма для ввода электронной почты.
# password_reset_done.html — сообщение о том, что письмо с инструкциями отправлено.
# password_reset_confirm.html — форма для ввода нового пароля.
# password_reset_complete.html — сообщение о том, что пароль успешно изменен.