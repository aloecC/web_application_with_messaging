from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from mailing import urls as mailing_urls
from users import urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("mailing/", include(mailing_urls, namespace='mailing')),
    path('users/', include('users.urls')),
]

#include() - Позволяет включать URL-шаблоны из других файлов

#Позволяет нашему серверу разработки обрабатывать и уводить загружаемые файлы через наш адрес указанный в MEDIA_ROOT
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)