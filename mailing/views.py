from datetime import timezone

from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic import ListView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse

from mailing.models import Message, Subscriber, Campaign, EmailAttempt


class MessageListView(ListView):
    model = Message
    template_name = 'mailing/messages_list.html'
    context_object_name = 'messages'


class MessageDetailView(DetailView):
    model = Message
    template_name = 'mailing/message_detail.html'
    context_object_name = 'message'

    def get_context_data(self, **kwargs):
        # Получаем контекст от родительского класса
        context = super().get_context_data(**kwargs)

        # Получаем сообщение из контекста
        message = self.object

        # Получаем подписчиков, связанных с этим сообщением
        context['subscribers'] = message.subscribers.all()

        return context


class MessageCreateView(CreateView):
    model = Message
    template_name = 'mailing/message_form.html'
    fields = ['subject', 'body', 'subscribers']
    success_url = reverse_lazy('mailing:message_list')


class MessageUpdateView(UpdateView):
    model = Message
    fields = ['subject', 'body', 'subscribers']
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')


class MessageDeleteView(DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')


class SubscriberListView(ListView):
    model = Subscriber
    template_name = 'mailing/subscriber_list.html'
    context_object_name = 'subscribers'

    def get_queryset(self):
        return Subscriber.objects.all()  # Получаем всех получателей


class SubscriberDetailView(DetailView):
    model = Subscriber
    template_name = 'mailing/subscriber_detail.html'
    context_object_name = 'subscriber'


class SubscriberCreateView(CreateView):
    model = Subscriber
    template_name = 'mailing/subscriber_form.html'
    fields = ['email', 'full_name', 'comment']
    success_url = reverse_lazy('mailing:subscriber_list')


class SubscriberUpdateView(UpdateView):
    model = Subscriber
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/subscriber_form.html'
    success_url = reverse_lazy('mailing:subscriber_list')


class SubscriberDeleteView(DeleteView):
    model = Subscriber
    template_name = 'mailing/subscriber_confirm_delete.html'
    success_url = reverse_lazy('mailing:subscriber_list')


class CampaignListView(ListView):
    model = Campaign
    template_name = 'mailing/home.html'
    context_object_name = 'campaignes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscribers'] = Subscriber.objects.all()
        context['campaignes'] = Campaign.objects.all()
        return context

    def get_queryset(self):
        return Campaign.objects.all()


class CampaignDetailView(DetailView):
    model = Campaign
    template_name = 'mailing/campaign_detail.html'
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_campaign = self.get_object()
        context['subscribers'] = current_campaign.subscribers.all()
        context['campaignes'] = Campaign.objects.all()
        return context

    def get_queryset(self):
        return Campaign.objects.all()


class CampaignCreateView(CreateView):
    model = Campaign
    template_name = 'mailing/campaign_form.html'
    fields = ['message', 'subscribers']
    success_url = reverse_lazy('mailing:campaign_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        print(f"Создана новая рассылка: {form.instance}")  # Отладочный вывод
        return response


class CampaignUpdateView(UpdateView):
    model = Campaign
    fields = ['message', 'subscribers']
    template_name = 'mailing/campaign_form.html'
    success_url = reverse_lazy('mailing:campaign_list')


class CampaignDeleteView(DeleteView):
    model = Campaign
    template_name = 'mailing/campaign_confirm_delete.html'
    success_url = reverse_lazy('mailing:campaign_list')


class StartEmailAttempt(View):
    template_name = 'mailing/campaign_detail.html'

    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)

        subscribers = campaign.subscribers.all()
        message = campaign.message.all()
        email_attempt = EmailAttempt(campaign=campaign)
        email_attempt.save()

        campaign.status = 'Запущена'
        campaign.start_time = timezone.now()
        campaign.save()

        for subscriber in subscribers:
            try:
                response = send_mail(
                    subject=f'{message.subject}',
                    message=f'{message.body}',
                    from_email='Subject here',
                    recipient_list=[subscriber.email],
                )
                # Если отправка успешна
                email_attempt.status = 'successful'

                email_attempt.server_response = f"Sent to {subscriber.full_name} with response {response}"
            except Exception as e:
                # Если произошла ошибка
                email_attempt.status = 'failed'
                email_attempt.server_response = str(e)

            # Сохраняем информацию о попытке
            email_attempt.save()

        campaign.status = 'Завершена'
        campaign.end_time = timezone.now()
        campaign.save()
        return JsonResponse({'status': 'Emails sent', 'campaign': campaign.name})

