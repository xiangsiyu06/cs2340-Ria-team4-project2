from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import (
    Education,
    JobSeekerProfile,
    ProfessionalLink,
    Project,
    User,
    WorkExperience,
)


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


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = (
            "institution",
            "degree",
            "field_of_study",
            "start_date",
            "end_date",
        )
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = (
            "company",
            "title",
            "description",
            "start_date",
            "end_date",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class ProfessionalLinkForm(forms.ModelForm):
    class Meta:
        model = ProfessionalLink
        fields = ("label", "url")
        widgets = {
            "label": forms.TextInput(
                attrs={"placeholder": "e.g. LinkedIn or GitHub"}
            ),
            "url": forms.URLInput(
                attrs={"placeholder": "https://example.com"}
            ),
        }

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("title", "description", "url")
        labels = {"url": "Link (optional)"}
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "e.g. Campus food delivery app"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 4, "placeholder": "What you built and the tools you used"}
            ),
            "url": forms.URLInput(
                attrs={"placeholder": "https://github.com/you/project"}
            ),
        }


class CandidateSearchForm(forms.Form):
    skills = forms.CharField(
        required=False,
        help_text="Comma-separated; candidates must have every skill, e.g. Python, SQL",
    )
    location = forms.CharField(required=False)
    project = forms.CharField(
        required=False,
        label="Project keyword",
        help_text="Matches project titles and descriptions, e.g. React or machine learning",
    )
