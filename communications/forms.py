from django import forms

from .models import Message


class MessageForm(forms.ModelForm):
    body = forms.CharField(
        label="Message",
        max_length=2000,
        strip=True,
        help_text="Up to 2,000 characters.",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Write a message…",
            }
        ),
    )

    class Meta:
        model = Message
        fields = ["body"]
