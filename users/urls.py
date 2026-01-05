from django.urls import path
from . import views
from .forms import CustomAuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView

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
    path('profile/edit/<str:username>/', UserProfileEditView.as_view(), name='edit_profile')
]
