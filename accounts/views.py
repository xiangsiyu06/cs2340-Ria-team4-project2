from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import role_required
from .forms import RegistrationForm
from .models import User


def register(request):
    form = RegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("accounts:registration_complete")

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def registration_complete(request):
    return render(request, "accounts/registration_complete.html")


@login_required
def dashboard(request):
    return render(request, "accounts/dashboard.html")


@role_required(User.Role.JOB_SEEKER)
def job_seeker_area(request):
    return render(request, "accounts/job_seeker_area.html")


@role_required(User.Role.RECRUITER)
def recruiter_area(request):
    return render(request, "accounts/recruiter_area.html")