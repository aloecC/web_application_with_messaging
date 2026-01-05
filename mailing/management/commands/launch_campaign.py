from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from mailing.models import Campaign, EmailAttempt


class Command(BaseCommand):
    help = 'Send email campaign'

    def add_arguments(self, parser):
        parser.add_argument('campaign_id', type=int, help='ID of the campaign to send')

    def handle(self, *args, **kwargs):
        campaign_id = kwargs['campaign_id']
        campaign = Campaign.objects.get(pk=campaign_id)

        # Проверка времени
        current_time = timezone.now()
        if not (campaign.start_time <= current_time <= campaign.end_time):
            self.stdout.write(self.style.ERROR('Рассылка не может быть запущена вне разрешенного времени.'))
            return

        # Определение получателей
        subscribers = campaign.subscribers.all()
        campaign.status = 'Запущена'
        campaign.save()

        for subscriber in subscribers:
            email_attempt = EmailAttempt(campaign=campaign, subscriber=subscriber)
            try:
                response = send_mail(
                    subject=campaign.message.subject,
                    message=campaign.message.body,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[subscriber.email],
                )
                # Если отправка успешна
                email_attempt.status = 'successful'
                email_attempt.server_response = f"Sent to {subscriber.full_name} with response {response}"
            except Exception as e:
                # Если произошла ошибка
                email_attempt.status = 'failed'
                email_attempt.server_response = str(e)

            email_attempt.save()

        campaign.status = 'Завершена'
        campaign.save()

        self.stdout.write(self.style.SUCCESS('Рассылка завершена успешно.'))