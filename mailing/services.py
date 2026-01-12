from .models import CustomUser


class MailingUsersService:
    from .models import CustomUser

    def get_user_blocked(self):
        """Возвращает список всех заблокированных пользователей."""
        return CustomUser.objects.filter(is_block=True)
