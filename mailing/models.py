from django.core.mail import send_mail
from django.db import models
from django.utils import timezone


class Subscriber(models.Model):
    '''Модель «Получатель рассылки»'''
    email = models.EmailField(unique=True, verbose_name='Почта')
    full_name = models.CharField(max_length=255, verbose_name='Ф.И.О.')
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    def __str__(self):
        return self.full_name


class Message(models.Model):
    '''Модель «Сообщение»'''
    subject = models.CharField(max_length=255, verbose_name='Тема письма')
    body = models.TextField(null=True, blank=True, verbose_name='Тело письма')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата и время последнего обновления')
    subscribers = models.ManyToManyField(Subscriber, related_name='messages')

    def __str__(self):
        return self.subject


class Campaign(models.Model):
    '''Модель «Рассылка»'''

    STATUS_CHOICES = [
        ('Создана', 'Создана'),
        ('Запущена', 'Запущена'),
        ('Завершена', 'Завершена'),
    ]

    message = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name='Сообщение')
    subscribers = models.ManyToManyField(Subscriber, related_name='campaigns', verbose_name='Получатели')
    first_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата и время первой отправки')
    end_time = models.DateTimeField(verbose_name='Дата и время окончания отправки', null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Создана', verbose_name='Статус')

    def __str__(self):
        return f"Рассылка: {self.message.subject} ({self.status})"

    def is_completed(self):
        return self.status == 'Завершена'

    def send_messages(self):
        if self.status != 'Запущена':
            self.status = 'Запущена'
            self.first_sent_at = timezone.now()
            self.save()

        response_status = "успешно"
        response_message = ""

        for subscriber in self.subscribers.all():
            try:
                send_mail(
                    self.message.subject,
                    self.message.body,
                    'from@example.com',  #адрес отправителя
                    [subscriber.email],
                    fail_silently=False,
                )
                # Логируем успешную попытку
                EmailAttempt.objects.create(campaign=self, subscriber=subscriber, status='успешно',
                                            response='Сообщение отправлено')
            except Exception as e:
                response_status = "не успешно"
                response_message = str(e)
                # Логируем неуспешную попытку
                EmailAttempt.objects.create(campaign=self, subscriber=subscriber, status='не успешно',
                                            response=response_message)

        if timezone.now() > self.end_time:
            self.status = 'Завершена'
            self.save()


class EmailAttempt(models.Model):
    '''Модель «Попытка отправки письма»'''
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, verbose_name='Рассылка')
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE, related_name='emails')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время попытки')
    status = models.CharField(max_length=20, verbose_name='Статус')
    response = models.TextField(verbose_name='Ответ почтового сервера')

    def __str__(self):
        return f"Попытка отправки для {self.subscriber.email} - {self.status}"
