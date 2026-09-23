from django import forms
from .models import Application, Job


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["note"]
        labels = {"note": "Personalized note (optional)"}
        help_texts = {"note": "Tell the hiring team why this role fits you. Up to 2,000 characters."}
        widgets = {"note": forms.Textarea(attrs={"rows": 4, "maxlength": 2000})}


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "title",
            "company",
            "description",
            "address",
            "salary_min",
            "salary_max",
            "remote_type",
            "visa_sponsorship",
            "skills",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def clean(self):
        cleaned = super().clean()
        lo = cleaned.get("salary_min")
        hi = cleaned.get("salary_max")
        if lo is not None and hi is not None and lo > hi:
            self.add_error("salary_max", "Max salary must be at least min salary.")
        return cleaned
