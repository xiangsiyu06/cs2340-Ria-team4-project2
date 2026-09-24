from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import JobSeekerProfile, User


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (User.Role.JOB_SEEKER, "Job Seeker"),
            (User.Role.RECRUITER, "Recruiter"),
        ]
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "role")


class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ("headline", "skills", "location")
        widgets = {
            "headline": forms.TextInput(
                attrs={"placeholder": "e.g. Aspiring software engineer"}
            ),
            "skills": forms.TextInput(
                attrs={"placeholder": "e.g. Python, Django, SQL"}
            ),
            "location": forms.TextInput(
                attrs={"placeholder": "e.g. Atlanta, GA"}
            ),
        }