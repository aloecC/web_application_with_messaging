from datetime import timezone
import tkinter as tk

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic import ListView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse
from pip._internal.models.link import Link

from config.settings import EMAIL_HOST_USER, DEFAULT_FROM_EMAIL
from mailing.forms import CampaignForm
from mailing.models import Message, Subscriber, Campaign, EmailAttempt
from users.models import CustomUser


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'mailing/messages_list.html'
    context_object_name = 'messages'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['count'] = self.get_count()
        return context

    def get_count(self):
        messages = Message.objects.all()
        count = 0
        for message in messages:
            count += 1
        return count


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'mailing/message_detail.html'
    context_object_name = 'message'

    def get_context_data(self, **kwargs):
        # Получаем контекст от родительского класса
        context = super().get_context_data(**kwargs)
        context['is_manager'] = self.request.user.is_staff or self.request.user.groups.filter(name='Менеджеры').exists()
        # Получаем сообщение из контекста
        message = self.object

        return context


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    template_name = 'mailing/message_form.html'
    fields = ['subject', 'body']
    success_url = reverse_lazy('mailing:message_list')


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    fields = ['subject', 'body']
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')


class SubscriberListView(LoginRequiredMixin, ListView):
    model = Subscriber
    template_name = 'mailing/subscriber_list.html'

    context_object_name = 'subscribers'

    def get_queryset(self):
        if self.request.user.groups.filter(name='Менеджер').exists():
            return Subscriber.objects.all()
        else:
            return Subscriber.objects.filter(owner=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['count'] = self.get_count()
        return context

    def get_count(self):
        subscribers = self.get_queryset()
        count = 0
        for subscriber in subscribers:
            count += 1
        return count

    def test_func(self):
        return True


class SubscriberDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Subscriber
    template_name = 'mailing/subscriber_detail.html'
    context_object_name = 'subscriber'

    def test_func(self):
        subscriber = self.get_object()
        if not self.request.user.groups.filter(name='Менеджер').exists() and not self.request.user.is_staff:
            return self.request.user == subscriber.owner
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        subscriber = self.get_object()
        context['is_manager'] = self.request.user.is_staff or self.request.user.groups.filter(name='Менеджер').exists()
        context['is_owner'] = self.request.user == subscriber.owner
        return context


class SubscriberCreateView(LoginRequiredMixin, CreateView):
    model = Subscriber
    template_name = 'mailing/subscriber_form.html'
    fields = ['email', 'full_name', 'comment']
    success_url = reverse_lazy('mailing:subscriber_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user  # Устанавливаем владельца на текущего пользователя
        return super().form_valid(form)


class SubscriberUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Subscriber
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/subscriber_form.html'
    success_url = reverse_lazy('mailing:subscriber_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['is_manager'] = self.request.user.is_staff or self.request.user.groups.filter(name='Менеджер').exists()
        return context

    def test_func(self):
        subscriber = self.get_object()
        return self.request.user == subscriber.owner


class SubscriberDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Subscriber
    template_name = 'mailing/subscriber_confirm_delete.html'
    success_url = reverse_lazy('mailing:subscriber_list')

    def test_func(self):
        subscriber = self.get_object()
        return self.request.user == subscriber.owner


class CampaignListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Campaign
    template_name = 'mailing/campaign_list.html'
    context_object_name = 'campaignes'

    def get_queryset(self):
        if self.request.user.groups.filter(name='Менеджер').exists():
            return Campaign.objects.all()
        else:
            return Campaign.objects.filter(owner=self.request.user)

    def get_active_status(self):
        campaignes = self.get_queryset()
        active_status = True
        for campaign in campaignes:
            active_status = campaign.status_active

        return active_status

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['count'] = self.get_count()
        context['is_manager'] = self.request.user.is_staff or self.request.user.groups.filter(name='Менеджер').exists()
        context['is_status_active'] = self.get_active_status()
        return context

    def get_count(self):
        campaignes = self.get_queryset()
        return campaignes.count()

    def test_func(self):
        return True


class CampaignView(LoginRequiredMixin, UserPassesTestMixin, View):
    model = Campaign
    template_name = 'mailing/home.html'
    context_object_name = 'campaignes'

    def get(self, request):
        campaigns = self.get_user_campaigns()
        subscribers = self.get_user_subscribers()
        active_campaigns = campaigns.filter(status='Запущена').count()

        if not self.request.user.groups.filter(name='Менеджер').exists():
            unique_recipients = subscribers.filter(owner=self.request.user).count()
        else:
            unique_recipients = subscribers.all().count()


        context = {
            'campaignes': campaigns,
            'total_campaigns': campaigns.count(),
            'active_campaigns': active_campaigns,
            'unique_recipients_count': unique_recipients,
            'is_manager': self.request.user.is_staff or self.request.user.groups.filter(name='Менеджер').exists(),
            'users_count': CustomUser.objects.all().count()
        }

        return render(request, self.template_name, context)

    def get_user_campaigns(self):
        if self.request.user.groups.filter(name='Менеджер').exists():
            return Campaign.objects.all()
        else:
            return Campaign.objects.filter(owner=self.request.user)

    def get_user_subscribers(self):
        if self.request.user.groups.filter(name='Менеджер').exists():
            return Subscriber.objects.all()
        else:
            return Subscriber.objects.filter(owner=self.request.user)

    def test_func(self):
        return True


class CampaignDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Подробная информация о рассылке"""
    model = Campaign
    template_name = 'mailing/campaign_detail.html'
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_campaign = self.get_object()
        campaign = self.get_object()
        user_owner = campaign.owner
        context['subscribers'] = current_campaign.subscribers.all()
        context['campaignes'] = Campaign.objects.all()
        context['is_manager'] = self.request.user.is_staff or self.request.user.groups.filter(name='Менеджер').exists()
        context['is_owner'] = self.request.user == user_owner,
        context['user_owner'] = user_owner
        return context

    def test_func(self):
        campaign = self.get_object()
        if not self.request.user.groups.filter(name='Менеджер').exists() and not self.request.user.is_staff:
            return self.request.user == campaign.owner
        return True


class CampaignCreateView(LoginRequiredMixin, CreateView):
    """Создание новой рассылки"""
    form_class = CampaignForm
    template_name = 'mailing/campaign_form.html'
    success_url = reverse_lazy('mailing:campaign_list')

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        # Логика для создания новой рассылки
        form = self.get_form()
        if form.is_valid():
            status_active = Campaign.objects.filter(status_active=True).exists()  # Проверяем, есть ли активные рассылки
            new_campaign = form.save(commit=False)  # Создаем объект, но не сохраняем его еще
            new_campaign.status_active = status_active  # Устанавливаем статус
            new_campaign.owner = request.user  # Устанавливаем владельца
            new_campaign.save()  # Сохраняем объект в базе данных

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class CampaignUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'mailing/campaign_form.html'
    success_url = reverse_lazy('mailing:campaign_list')

    def test_func(self):
        campaign = self.get_object()
        return self.request.user == campaign.owner


class CampaignDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Campaign
    template_name = 'mailing/campaign_confirm_delete.html'
    success_url = reverse_lazy('mailing:campaign_list')

    def test_func(self):
        campaign = self.get_object()
        if not self.request.user.groups.filter(name='Менеджер').exists() and not self.request.user.is_staff:
            return self.request.user == campaign.owner
        return True


class StartEmailAttemptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        campaign = get_object_or_404(Campaign, pk=pk)
        subscribers = campaign.subscribers.all()

        campaign.status = 'Запущена'
        campaign.save()

        for subscriber in subscribers:
            email_attempt = EmailAttempt(campaign=campaign, subscriber=subscriber)
            email_attempt.owner = self.request.user
            try:
                response = send_mail(
                    subject=f'{ campaign.message.subject }',
                    message=f'{ campaign.message.body }',
                    from_email=f'{ EMAIL_HOST_USER }',
                    recipient_list=[subscriber.email],
                )
                # Если отправка успешна
                email_attempt.status = 'successful'
                email_attempt.subscriber = subscriber

                email_attempt.response = f"Sent to {subscriber.full_name} with response {response}"
            except Exception as e:
                # Если произошла ошибка
                email_attempt.status = 'failed'
                email_attempt.response = str(e)

                # Сохраняем информацию о попытке
            email_attempt.subscriber = subscriber
            email_attempt.save()

        campaign.status = 'Завершена'
        campaign.save()

        return redirect('mailing:campaign_detail', pk=pk)


class StopEmailAttemptView(View):
    def post(self, request, pk):
        campaign = get_object_or_404(Campaign, pk=pk)
        campaign.status = 'Завершена'
        campaign.save()

        return redirect('mailing:campaign_detail', pk=pk)


class EmailAttemptListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = EmailAttempt
    template_name = 'mailing/emailattempt_list.html'
    context_object_name = 'emailattempts'

    def get_queryset(self):
        if self.request.user.groups.filter(name='Менеджер').exists():
            return EmailAttempt.objects.all()
        else:
            return EmailAttempt.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emailattempts = self.get_queryset()

        count_successful = emailattempts.filter(status='successful').count()
        count_failed = emailattempts.filter(status='failed').count()
        count_all = emailattempts.all().count()

        context['count_successful'] = count_successful
        context['count_failed'] = count_failed
        context['count_all'] = count_all

        return context

    def test_func(self):
        return True


class EmailAttemptSuccessfulListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = EmailAttempt
    template_name = 'mailing/emailattempt_list_successful.html'
    context_object_name = 'emailattempts'

    def get_queryset(self):
        if self.request.user.groups.filter(name='Менеджер').exists():
            return EmailAttempt.objects.filter(status='successful')
        else:
            return EmailAttempt.objects.filter(owner=self.request.user, status='successful')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emailattempts = self.get_queryset()

        count_successful = emailattempts.all().count()

        context['emailattempts'] = emailattempts
        context['count_successful'] = count_successful

        return context

    def test_func(self):
        return True


class EmailAttemptFailedListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = EmailAttempt
    template_name = 'mailing/emailattempt_list_failed.html'
    context_object_name = 'emailattempts'

    def get_queryset(self):
        if self.request.user.groups.filter(name='Менеджер').exists():
            return EmailAttempt.objects.filter(status='failed')
        else:
            return EmailAttempt.objects.filter(owner=self.request.user, status='failed')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emailattempts = self.get_queryset()

        count_failed = emailattempts.all().count()

        context['emailattempts'] = emailattempts
        context['count_failed'] = count_failed

        return context

    def test_func(self):
        return True


class EmailAttemptDeleteView(LoginRequiredMixin, UserPassesTestMixin,  DeleteView):
    model = EmailAttempt
    template_name = 'mailing/emailattempt_confirm_delete.html'
    success_url = reverse_lazy('mailing:emailattempt_list')

    def test_func(self):
        emailattempt = self.get_object()
        if not self.request.user.groups.filter(name='Менеджер').exists() and not self.request.user.is_staff:
            return self.request.user == emailattempt.owner
        return True


class EmailAttemptDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = EmailAttempt
    template_name = 'mailing/emailattempt_detail.html'
    context_object_name = 'emailattempt'

    def test_func(self):
        emailattempt = self.get_object()
        if not self.request.user.groups.filter(name='Менеджер').exists() and not self.request.user.is_staff:
            return self.request.user == emailattempt.owner
        return True


class ContactsTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'mailing/contacts.html'
    success_url = reverse_lazy('mailing:contacts')

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        message = request.POST.get('message')
        email = request.POST.get('email')


        subject = 'Поддержка'
        message = f'Сообщение:"{message}". Электронная почта для связи: {email}({name}).'
        from_email = DEFAULT_FROM_EMAIL
        recipient_list = [DEFAULT_FROM_EMAIL,]
        send_mail(subject, message, from_email, recipient_list)

        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class CampaignBreakAllView(View):
    """Отключение рассылок"""
    def post(self, request):
        campaigns = Campaign.objects.all()
        for campaign in campaigns:
            campaign.status_active = False
            campaign.save()

        return redirect('mailing:campaign_list')


class CampaignStartAllView(View):
    """Включение рассылок"""
    def post(self, request):
        campaigns = Campaign.objects.all()
        for campaign in campaigns:
            campaign.status_active = True
            campaign.save()

        return redirect('mailing:campaign_list')

