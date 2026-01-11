from django.core.management.base import BaseCommand
from users.models import TemporaryUser
from django.utils import timezone


class Command(BaseCommand):
    help = 'Удаляет временных пользователей с истекшим сроком действия'

    def handle(self, *args, **kwargs):
        expired_users = TemporaryUser.objects.filter(created_at__lt=timezone.now() - timezone.timedelta(minutes=5))
        expired_users.delete()
        self.stdout.write(self.style.SUCCESS(f'Удалено {expired_users.count()} устаревших временных пользователей.'))
