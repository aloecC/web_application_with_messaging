import os
from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions

from .models import Campaign, Subscriber


class CampaignForm(forms.ModelForm):

    class Meta:
        model = Campaign
        fields = ["message", "subscribers", "start_time", "end_time"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(CampaignForm, self).__init__(*args, **kwargs)

        if user:
            self.fields["subscribers"].queryset = Subscriber.objects.filter(owner=user)

        self.fields["message"].widget.attrs.update({"class": "form-control", "placeholder": "Выберите сообщение"})

        self.fields["subscribers"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Выберите получателей"}
        )

        self.fields["start_time"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Введите дату и время начала отправки в формате YYYY-MM-DD HH:MM",
            }
        )

        self.fields["end_time"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Введите дату и время конца отправки в формате YYYY-MM-DD HH:MM",
            }
        )
