from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic import ListView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse

from mailing.models import Message, Subscriber, Campaign


class MessageListView(ListView):
    model = Message
    template_name = 'mailing/home.html'
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
    template_name = 'mailing/subscriber_home.html'
    context_object_name = 'subscribers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['campaignes'] = Campaign.objects.all()  # Получаем все кампании
        return context

    def get_queryset(self):
        return Subscriber.objects.all()  # Получаем всех подписчиков


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
    template_name = 'mailing/subscriber_home.html'
    context_object_name = 'campaignes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscribers'] = Subscriber.objects.all()
        return context

    def get_queryset(self):
        return Campaign.objects.all()


class CampaignDetailView(DetailView):
    model = Campaign
    template_name = 'mailing/campaign_detail.html'
    context_object_name = 'campaign'


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

