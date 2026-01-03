from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.create(
            email='derevo@mail.com',
            first_name='Admin',
            last_name='Admin',

        )

        user.set_password('12345')

        user.is_staff = True
        user.is_superuser = True

        user.save()

        self.stdout.write(self.style.SUCCESS('Администратор успешно создан'))

        # Получение разрешений
        delete_permission = Permission.objects.get(codename='delete_user')

