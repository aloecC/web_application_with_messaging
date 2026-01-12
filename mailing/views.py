import tkinter as tk
from datetime import timezone

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from config.settings import DEFAULT_FROM_EMAIL, EMAIL_HOST_USER
from mailing.forms import CampaignForm
from mailing.models import Campaign, EmailAttempt, Message, Subscriber
from users.models import CustomUser


@method_decorator(cache_page(60 * 15), name="dispatch")
class MessageListView(LoginRequiredMixin, ListView):
    """Отображение списка сообщений"""

    model = Message
    template_name = "mailing/messages_list.html"
    context_object_name = "messages"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["count"] = self.get_count()
        return context

    def get_count(self):
        messages = self.get_queryset()
        count = 0
        for message in messages:
            count += 1
        return count

    def get_queryset(self):
        queryset = cache.get("my_message_list")
        if not queryset:
            queryset = Message.objects.all()
            cache.set("my_message_list", queryset, 60 * 15)
        return queryset


@method_decorator(cache_page(60 * 15), name="dispatch")
class MessageDetailView(LoginRequiredMixin, DetailView):
    """Подробная информация о сообщении"""

    model = Message
    template_name = "mailing/message_detail.html"
    context_object_name = "message"

    def get_context_data(self, **kwargs):
        # Получаем контекст от родительского класса
        context = super().get_context_data(**kwargs)
        context["is_manager"] = (
            self.request.user.is_staff or self.request.user.groups.filter(name="Менеджеры").exists()
        )
        # Получаем сообщение из контекста
        message = self.object

        return context


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание сообщения"""

    model = Message
    template_name = "mailing/message_form.html"
    fields = ["subject", "body"]
    success_url = reverse_lazy("mailing:message_list")


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    """Обновление сообщения"""

    model = Message
    fields = ["subject", "body"]
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление сообщения"""

    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")


class SubscriberListView(LoginRequiredMixin, ListView):
    """Отображение списка получателей"""

    model = Subscriber
    template_name = "mailing/subscriber_list.html"

    context_object_name = "subscribers"

    def get_queryset(self):
        queryset = cache.get("my_subscriber_list")
        if not queryset:
            if self.request.user.groups.filter(name="Менеджер").exists():
                queryset = Subscriber.objects.all()
            else:
                queryset = Subscriber.objects.filter(owner=self.request.user)
            cache.set("my_subscriber_list", queryset, 60 * 15)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["count"] = self.get_count()
        return context

    def get_count(self):
        subscribers = self.get_queryset()
        count = 0
        for subscriber in subscribers:
            count += 1
        return count

    def test_func(self):
        return True


@method_decorator(cache_page(60 * 15), name="dispatch")
class SubscriberDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Подробная информация о получатели"""

    model = Subscriber
    template_name = "mailing/subscriber_detail.html"
    context_object_name = "subscriber"

    def test_func(self):
        subscriber = self.get_object()
        if not self.request.user.groups.filter(name="Менеджер").exists() and not self.request.user.is_staff:
            return self.request.user == subscriber.owner
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        subscriber = self.get_object()
        context["is_manager"] = self.request.user.is_staff or self.request.user.groups.filter(name="Менеджер").exists()
        context["is_owner"] = self.request.user == subscriber.owner
        return context


class SubscriberCreateView(LoginRequiredMixin, CreateView):
    """Создание получателя"""

    model = Subscriber
    template_name = "mailing/subscriber_form.html"
    fields = ["email", "full_name", "comment"]
    success_url = reverse_lazy("mailing:subscriber_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user  # Устанавливаем владельца на текущего пользователя
        return super().form_valid(form)


class SubscriberUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Обновление получателя"""

    model = Subscriber
    fields = ["email", "full_name", "comment"]
    template_name = "mailing/subscriber_form.html"
    success_url = reverse_lazy("mailing:subscriber_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["is_manager"] = self.request.user.is_staff or self.request.user.groups.filter(name="Менеджер").exists()
        return context

    def test_func(self):
        subscriber = self.get_object()
        return self.request.user == subscriber.owner


class SubscriberDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление получателя"""

    model = Subscriber
    template_name = "mailing/subscriber_confirm_delete.html"
    success_url = reverse_lazy("mailing:subscriber_list")

    def test_func(self):
        subscriber = self.get_object()
        return self.request.user == subscriber.owner


class CampaignListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Отображение списка рассылок"""

    model = Campaign
    template_name = "mailing/campaign_list.html"
    context_object_name = "campaignes"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Менеджер").exists():
            queryset = Campaign.objects.all()
        else:
            queryset = Campaign.objects.filter(owner=self.request.user)
        return queryset

    def get_active_status(self):
        """Получение статуса возможности запуска рассылки"""
        campaignes = self.get_queryset()
        active_status = True
        for campaign in campaignes:
            active_status = campaign.status_active

        return active_status

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["count"] = self.get_count()
        context["is_manager"] = self.request.user.is_staff or self.request.user.groups.filter(name="Менеджер").exists()
        context["is_status_active"] = self.get_active_status()
        return context

    def get_count(self):
        """Получение количества рассылок"""
        campaignes = self.get_queryset()
        return campaignes.count()

    def test_func(self):
        return True


class CampaignListActiveView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Отображение списка активных рассылок"""

    model = Campaign
    template_name = "mailing/campaign_list_active.html"
    context_object_name = "campaignes"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Менеджер").exists():
            queryset = Campaign.objects.filter(status="Запущена")
        else:
            queryset = Campaign.objects.filter(owner=self.request.user, status="Запущена")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["count"] = self.get_count()
        context["is_manager"] = self.request.user.is_staff or self.request.user.groups.filter(name="Менеджер").exists()
        return context

    def get_count(self):
        """Получение количества рассылок"""
        campaignes = self.get_queryset()
        return campaignes.count()

    def test_func(self):
        return True


class CampaignListCreatedView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Отображение списка созданных рассылок"""

    model = Campaign
    template_name = "mailing/campaign_list_created.html"
    context_object_name = "campaignes"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Менеджер").exists():
            queryset = Campaign.objects.filter(status="Создана")
        else:
            queryset = Campaign.objects.filter(owner=self.request.user, status="Создана")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["count"] = self.get_count()
        context["is_manager"] = self.request.user.is_staff or self.request.user.groups.filter(name="Менеджер").exists()
        return context

    def get_count(self):
        """Получение количества рассылок"""
        campaignes = self.get_queryset()
        return campaignes.count()

    def test_func(self):
        return True


class CampaignListCompletedView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Отображение списка завершенных рассылок"""

    model = Campaign
    template_name = "mailing/campaign_list_completed.html"
    context_object_name = "campaignes"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Менеджер").exists():
            queryset = Campaign.objects.filter(status="Завершена")
        else:
            queryset = Campaign.objects.filter(owner=self.request.user, status="Завершена")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["count"] = self.get_count()
        context["is_manager"] = self.request.user.is_staff or self.request.user.groups.filter(name="Менеджер").exists()
        return context

    def get_count(self):
        """Получение количества рассылок"""
        campaignes = self.get_queryset()
        return campaignes.count()

    def test_func(self):
        return True


@method_decorator(cache_page(60 * 15), name="dispatch")
class CampaignView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Отображение главной страницы"""

    model = Campaign
    template_name = "mailing/home.html"
    context_object_name = "campaignes"

    def get(self, request):
        campaigns = self.get_user_campaigns()
        subscribers = self.get_user_subscribers()
        active_campaigns = campaigns.filter(status="Запущена").count()

        if not self.request.user.groups.filter(name="Менеджер").exists():
            unique_recipients = subscribers.filter(owner=self.request.user).count()
        else:
            unique_recipients = subscribers.all().count()

        context = {
            "campaignes": campaigns,
            "total_campaigns": campaigns.count(),
            "active_campaigns": active_campaigns,
            "unique_recipients_count": unique_recipients,
            "is_manager": self.request.user.is_staff or self.request.user.groups.filter(name="Менеджер").exists(),
            "users_count": CustomUser.objects.all().count(),
        }

        return render(request, self.template_name, context)

    def get_user_campaigns(self):
        """Получение рассылок пользователя"""
        if self.request.user.groups.filter(name="Менеджер").exists():
            return Campaign.objects.all()
        else:
            return Campaign.objects.filter(owner=self.request.user)

    def get_user_subscribers(self):
        """Получение получателей пользователя"""
        if self.request.user.groups.filter(name="Менеджер").exists():
            return Subscriber.objects.all()
        else:
            return Subscriber.objects.filter(owner=self.request.user)

    def test_func(self):
        return True


class CampaignDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Подробная информация о рассылке"""

    model = Campaign
    template_name = "mailing/campaign_detail.html"
    context_object_name = "campaign"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_campaign = self.get_object()
        campaign = self.get_object()
        user_owner = campaign.owner
        context["subscribers"] = current_campaign.subscribers.all()
        context["campaignes"] = Campaign.objects.all()
        context["is_manager"] = self.request.user.is_staff or self.request.user.groups.filter(name="Менеджер").exists()
        context["is_owner"] = (self.request.user == user_owner,)
        context["user_owner"] = user_owner
        return context

    def test_func(self):
        campaign = self.get_object()
        if not self.request.user.groups.filter(name="Менеджер").exists() and not self.request.user.is_staff:
            return self.request.user == campaign.owner
        return True


class CampaignCreateView(LoginRequiredMixin, CreateView):
    """Создание новой рассылки"""

    form_class = CampaignForm
    template_name = "mailing/campaign_form.html"
    success_url = reverse_lazy("mailing:campaign_list")

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        # Логика для создания новой рассылки
        form = self.get_form()
        if form.is_valid():
            status_active = Campaign.objects.filter(
                status_active=True
            ).exists()  # Проверяем, есть ли активные рассылки
            new_campaign = form.save(commit=False)
            new_campaign.status_active = status_active
            new_campaign.owner = request.user
            new_campaign.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class CampaignUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Обновление рассылки"""

    model = Campaign
    form_class = CampaignForm
    template_name = "mailing/campaign_form.html"
    success_url = reverse_lazy("mailing:campaign_list")

    def test_func(self):
        campaign = self.get_object()
        return self.request.user == campaign.owner

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class CampaignDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление рассылки"""

    model = Campaign
    template_name = "mailing/campaign_confirm_delete.html"
    success_url = reverse_lazy("mailing:campaign_list")

    def test_func(self):
        campaign = self.get_object()
        if not self.request.user.groups.filter(name="Менеджер").exists() and not self.request.user.is_staff:
            return self.request.user == campaign.owner
        return True


class StartEmailAttemptView(LoginRequiredMixin, View):
    """Запуск(создание обьектов 'Попытка рассылки') рассылки"""

    def post(self, request, pk):
        campaign = get_object_or_404(Campaign, pk=pk)
        subscribers = campaign.subscribers.all()

        campaign.status = "Запущена"
        campaign.save()

        for subscriber in subscribers:
            email_attempt = EmailAttempt(campaign=campaign, subscriber=subscriber)
            email_attempt.owner = self.request.user
            try:
                response = send_mail(
                    subject=f"{ campaign.message.subject }",
                    message=f"{ campaign.message.body }",
                    from_email=f"{ EMAIL_HOST_USER }",
                    recipient_list=[subscriber.email],
                )
                # Если отправка успешна
                email_attempt.status = "successful"
                email_attempt.subscriber = subscriber

                email_attempt.response = f"Sent to {subscriber.full_name} with response {response}"
            except Exception as e:
                # Если произошла ошибка
                email_attempt.status = "failed"
                email_attempt.response = str(e)

                # Сохраняем информацию о попытке
            email_attempt.subscriber = subscriber
            email_attempt.save()

        campaign.status = "Завершена"
        campaign.save()

        return redirect("mailing:campaign_detail", pk=pk)


class StopEmailAttemptView(View):
    """Прерывание запуска(создание обьектов 'Попытка рассылки') рассылки"""

    def post(self, request, pk):
        campaign = get_object_or_404(Campaign, pk=pk)
        campaign.status = "Завершена"
        campaign.save()

        return redirect("mailing:campaign_detail", pk=pk)


class EmailAttemptListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Отображение отчетов по рассылкам"""

    model = EmailAttempt
    template_name = "mailing/emailattempt_list.html"
    context_object_name = "emailattempts"

    def get_queryset(self):
        queryset = cache.get("my_email_attempt_list")
        if not queryset:
            if self.request.user.groups.filter(name="Менеджер").exists():
                queryset = EmailAttempt.objects.all()
            else:
                queryset = EmailAttempt.objects.filter(owner=self.request.user)
        cache.set("my_email_attempt_list", queryset, 60 * 15)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emailattempts = self.get_queryset()

        count_successful = emailattempts.filter(status="successful").count()
        count_failed = emailattempts.filter(status="failed").count()
        count_all = emailattempts.all().count()

        context["count_successful"] = count_successful
        context["count_failed"] = count_failed
        context["count_all"] = count_all

        return context

    def test_func(self):
        return True


class EmailAttemptSuccessfulListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Отображение списка успешных попыток рассылки"""

    model = EmailAttempt
    template_name = "mailing/emailattempt_list_successful.html"
    context_object_name = "emailattempts"

    def get_queryset(self):
        queryset = cache.get("my_email_attempt_successful_list")
        if not queryset:
            if self.request.user.groups.filter(name="Менеджер").exists():
                queryset = EmailAttempt.objects.filter(status="successful")
            else:
                queryset = EmailAttempt.objects.filter(owner=self.request.user, status="successful")
        cache.set("my_email_attempt_successful_list", queryset, 60 * 15)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emailattempts = self.get_queryset()

        count_successful = emailattempts.all().count()

        context["emailattempts"] = emailattempts
        context["count_successful"] = count_successful

        return context

    def test_func(self):
        return True


class EmailAttemptFailedListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Отображение списка не успешных попыток рассылки"""

    model = EmailAttempt
    template_name = "mailing/emailattempt_list_failed.html"
    context_object_name = "emailattempts"

    def get_queryset(self):
        queryset = cache.get("my_email_attempt_failed_list")
        if not queryset:
            if self.request.user.groups.filter(name="Менеджер").exists():
                queryset = EmailAttempt.objects.filter(status="failed")
            else:
                queryset = EmailAttempt.objects.filter(owner=self.request.user, status="failed")
        cache.set("my_email_attempt_failed_list", queryset, 60 * 15)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emailattempts = self.get_queryset()

        count_failed = emailattempts.all().count()

        context["emailattempts"] = emailattempts
        context["count_failed"] = count_failed

        return context

    def test_func(self):
        return True


class EmailAttemptDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = EmailAttempt
    template_name = "mailing/emailattempt_confirm_delete.html"
    success_url = reverse_lazy("mailing:emailattempt_list")

    def test_func(self):
        emailattempt = self.get_object()
        if not self.request.user.groups.filter(name="Менеджер").exists() and not self.request.user.is_staff:
            return self.request.user == emailattempt.owner
        return True


@method_decorator(cache_page(60 * 15), name="dispatch")
class EmailAttemptDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Подробная информация об отчете"""

    model = EmailAttempt
    template_name = "mailing/emailattempt_detail.html"
    context_object_name = "emailattempt"

    def test_func(self):
        emailattempt = self.get_object()
        if not self.request.user.groups.filter(name="Менеджер").exists() and not self.request.user.is_staff:
            return self.request.user == emailattempt.owner
        return True


@method_decorator(cache_page(60 * 15), name="dispatch")
class ContactsTemplateView(LoginRequiredMixin, TemplateView):
    template_name = "mailing/contacts.html"
    success_url = reverse_lazy("mailing:contacts")

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name")
        message = request.POST.get("message")
        email = request.POST.get("email")

        subject = "Поддержка"
        message = f'Сообщение:"{message}". Электронная почта для связи: {email}({name}).'
        from_email = DEFAULT_FROM_EMAIL
        recipient_list = [
            DEFAULT_FROM_EMAIL,
        ]
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
            print("Статус изменен")
            campaign.save()
        print("Рассылка выключена")
        return redirect("mailing:campaign_list")


class CampaignStartAllView(View):
    """Включение рассылок"""

    def post(self, request):
        campaigns = Campaign.objects.all()
        for campaign in campaigns:
            campaign.status_active = True
            print("Статус изменен")
            campaign.save()
        print("Рассылка включена")
        return redirect("mailing:campaign_list")
