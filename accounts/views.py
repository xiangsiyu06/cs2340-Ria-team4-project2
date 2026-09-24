import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .decorators import role_required
from .forms import JobSeekerProfileForm, RegistrationForm
from .models import JobSeekerProfile, User


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

@role_required(User.Role.JOB_SEEKER)
def edit_job_seeker_profile(request):
    profile = JobSeekerProfile.objects.filter(user=request.user).first()

    form = JobSeekerProfileForm(
        request.POST or None,
        instance=profile,
    )

    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()

        messages.success(request, "Your profile has been saved.")
        return redirect("accounts:job_seeker_area")

    return render(
        request,
        "accounts/profile_form.html",
        {"form": form},
    )


@role_required(User.Role.RECRUITER)
def recruiter_area(request):
    return render(request, "accounts/recruiter_area.html")


@role_required(User.Role.ADMINISTRATOR)
def reporting(request):
    """Show administrators a privacy-conscious summary of account usage."""
    account_counts = User.objects.aggregate(
        total=Count("id"),
        job_seekers=Count(
            "id",
            filter=Q(role=User.Role.JOB_SEEKER),
        ),
        recruiters=Count(
            "id",
            filter=Q(role=User.Role.RECRUITER),
        ),
        administrators=Count(
            "id",
            filter=Q(role=User.Role.ADMINISTRATOR),
        ),
    )
    return render(
        request,
        "accounts/reporting.html",
        {"account_counts": account_counts},
    )


def _spreadsheet_safe(value):
    """Prevent text cells from being interpreted as spreadsheet formulas."""
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{text}"
    return text


def _csv_datetime(value):
    """Return a stable, timezone-aware ISO 8601 string for CSV output."""
    if value is None:
        return ""
    return value.isoformat()


@role_required(User.Role.ADMINISTRATOR)
def export_users_csv(request):
    """Download a minimal account-usage dataset for administrator reporting."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    filename = (
        f"careerbridge-user-report-{timezone.localdate().isoformat()}.csv"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"

    writer = csv.writer(response, lineterminator="\n")
    writer.writerow(
        [
            "user_id",
            "username",
            "role",
            "is_active",
            "date_joined",
            "last_login",
        ]
    )

    users = User.objects.order_by("id").iterator()
    for user in users:
        writer.writerow(
            [
                user.pk,
                _spreadsheet_safe(user.username),
                user.role,
                user.is_active,
                _csv_datetime(user.date_joined),
                _csv_datetime(user.last_login),
            ]
        )

    return response
