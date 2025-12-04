from django.contrib import admin

from mailing.models import Campaign, EmailAttempt, Subscriber, Message


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = (id, 'email', 'full_name', 'comment')
    list_filter = ('email',)  # Фильтрация
    search_fields = ('email', 'full_name',)  # Поиск


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (id, 'subject', 'body', 'created_at', 'updated_at')
    list_filter = ('subject',)  # Фильтрация
    search_fields = ('subject', 'body',)  # Поиск


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (id, 'message', 'first_sent_at', 'end_time', 'status')
    list_filter = ('status',)  # Фильтрация
    search_fields = ('status', 'message',)  # Поиск


@admin.register(EmailAttempt)
class EmailAttemptAdmin(admin.ModelAdmin):
    list_display = (id, 'campaign', 'subscriber', 'sent_at', 'status', 'response')
    list_filter = ('status',)  # Фильтрация
    search_fields = ('campaign', 'subscriber',)  # Поиск
