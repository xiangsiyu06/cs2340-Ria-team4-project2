# Create your views here.
from django.shortcuts import redirect, render

from .forms import RegistrationForm


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
