from django.urls import path
from . import views
from .views import MessageDeleteView, MessageUpdateView, MessageCreateView, MessageDetailView, MessageListView, \
    SubscriberListView, SubscriberDeleteView, SubscriberUpdateView, SubscriberCreateView, SubscriberDetailView, \
    CampaignCreateView, CampaignDetailView, CampaignUpdateView, CampaignDeleteView, CampaignListView

#Пространство имен(помогает избежать ошибки при одинаковых именах маршрута)
app_name = 'mailing'

#В urlpatterns создаются и регестрируются маршруты
#Path это специальная функция которая позволяет регестрировать наш маршрут


urlpatterns = [
    path('messages/', MessageListView.as_view(), name='message_list'), #ok
    path('message/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),#Ok
    path('message/new/', MessageCreateView.as_view(), name='message_create'),#Ok
    path('message/<int:pk>/edit/', MessageUpdateView.as_view(), name='message_edit'), #ok
    path('message/<int:pk>/delete/', MessageDeleteView.as_view(), name='message_delete'),#ok
    path('subscribers/', SubscriberListView.as_view(), name='subscriber_list'), #ok
    path('subscriber/<int:pk>/', SubscriberDetailView.as_view(), name='subscriber_detail'),#ok
    path('subscriber/new/', SubscriberCreateView.as_view(), name='subscriber_create'),#ok
    path('subscriber/<int:pk>/edit/', SubscriberUpdateView.as_view(), name='subscriber_edit'),#ok
    path('subscriber/<int:pk>/delete/', SubscriberDeleteView.as_view(), name='subscriber_delete'),#ok
    path('campaign/<int:pk>/', CampaignDetailView.as_view(), name='campaign_detail'),
    path('campaign/new/', CampaignCreateView.as_view(), name='campaign_create'),
    path('home/', CampaignListView.as_view(), name='campaign_list'),
    path('campaign/<int:pk>/edit/', CampaignUpdateView.as_view(), name='campaign_edit'),
    path('campaign/<int:pk>/delete/', CampaignDeleteView.as_view(), name='campaign_delete'),
]