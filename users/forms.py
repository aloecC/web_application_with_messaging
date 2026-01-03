from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False)
    username = forms.CharField(max_length=50, required=True)
    usable_password = None

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

