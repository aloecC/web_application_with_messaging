import random

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.mail import send_mail

from config import settings
from .models import CustomUser


class VerificationCodeForm(forms.Form):
    verification_code = forms.CharField(label='Код подтверждения', max_length=6)

    class Meta:
        fields = ('verification_code')

    def __init__(self, *args, **kwargs):
        super(VerificationCodeForm, self).__init__(*args, **kwargs)

        self.fields['email'].widget.attrs.update(
            {
                'class': 'form-control',
                'type': 'email',
                'placeholder': 'Введите код подтверждения'
            }
        )

    def clean_verification_code(self):
        code = self.verification_code
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Код должен состоять из 6 цифр.")
        if code != CustomUserCreationForm.verification_code:
            raise forms.ValidationError("Неверный код подтверждения.")
        return code


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False)
    username = forms.CharField(max_length=50, required=True)
    usable_password = None
    verification_code = forms.CharField(max_length=6, required=False, label='Код подтверждения')

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)

        self.fields['email'].widget.attrs.update(
            {
                'class': 'form-control',
                'type': 'email',
                'placeholder': 'Введите почту'
            }
        )

        self.fields['username'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': 'Введите ник'
            }
        )

        self.fields['first_name'].widget.attrs.update(
            {
                'class': 'form-control',
                'type': 'text',
                'placeholder': 'Введите ваше имя'
            }
        )

        self.fields['phone_number'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': 'Введите ваш номер',
            }
        )

        self.fields['password1'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': 'Введите ваш пароль'
            }
        )

        self.fields['password2'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': 'Повторно введите ваш пароль'
            }
        )

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and not phone_number.isdigit():
            raise forms.ValidationError('номер телефона должен остоять только их цифр')
        return phone_number

    def send_verification_email(self):
        user_email = self.cleaned_data.get('email')
        verification_code = str(random.randint(100000, 999999))  # Генерация 6-значного кода
        # Сохраните код в пользовательской модели или сессии для дальнейшей проверки
        self.verification_code = verification_code

        # Отправка письма
        send_mail(
            'Ваш код подтверждения',
            f'Ваш код подтверждения: {verification_code}',
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Введите почту'
    }))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Введите ваш пароль'
    }))

    class Meta:
        fields = ('username', 'password')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['avatar', 'email', 'username', 'first_name', 'phone_number']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

        self.fields['email'].widget.attrs.update(
            {
                'class': 'form-control',
                'type': 'email',
                'placeholder': 'Введите почту'
            }
        )

        self.fields['username'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': 'Введите ник'
            }
        )

        self.fields['first_name'].widget.attrs.update(
            {
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Введите ваше имя'
            }
        )

        self.fields['phone_number'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': 'Введите ваш номер',
            }
        )

