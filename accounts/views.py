import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from jobs.models import Application, Job

from .decorators import role_required
from .forms import EducationForm, JobSeekerProfileForm, RegistrationForm
from .models import Education, JobSeekerProfile, User


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
    profile = JobSeekerProfile.objects.filter(user=request.user).first()

    if profile:
        education_records = profile.education_records.all()
    else:
        education_records = Education.objects.none()

    return render(
        request,
        "accounts/job_seeker_area.html",
        {
            "profile": profile,
            "education_records": education_records,
        },
    )



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
    job_counts = Job.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=Job.Status.ACTIVE)),
        removed=Count("id", filter=Q(status=Job.Status.REMOVED)),
    )
    return render(
        request,
        "accounts/reporting.html",
        {
            "account_counts": account_counts,
            "job_counts": job_counts,
            "application_count": Application.objects.count(),
        },
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


@role_required(User.Role.ADMINISTRATOR)
def export_jobs_csv(request):
    """Download job-post activity without exposing application content."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    filename = f"careerbridge-job-report-{timezone.localdate().isoformat()}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"

    writer = csv.writer(response, lineterminator="\n")
    writer.writerow(
        [
            "job_id",
            "title",
            "company",
            "recruiter_username",
            "remote_type",
            "status",
            "created_at",
        ]
    )
    jobs = Job.objects.select_related("recruiter").order_by("id").iterator()
    for job in jobs:
        writer.writerow(
            [
                job.pk,
                _spreadsheet_safe(job.title),
                _spreadsheet_safe(job.company),
                _spreadsheet_safe(job.recruiter.username),
                job.remote_type,
                job.status,
                _csv_datetime(job.created_at),
            ]
        )

    return response


@role_required(User.Role.ADMINISTRATOR)
def export_applications_csv(request):
    """Download application activity while excluding private applicant notes."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    filename = (
        f"careerbridge-application-report-{timezone.localdate().isoformat()}.csv"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"

    writer = csv.writer(response, lineterminator="\n")
    writer.writerow(
        [
            "application_id",
            "job_id",
            "job_title",
            "company",
            "applicant_username",
            "created_at",
        ]
    )
    applications = (
        Application.objects.select_related("job", "applicant")
        .order_by("id")
        .iterator()
    )
    for application in applications:
        writer.writerow(
            [
                application.pk,
                application.job_id,
                _spreadsheet_safe(application.job.title),
                _spreadsheet_safe(application.job.company),
                _spreadsheet_safe(application.applicant.username),
                _csv_datetime(application.created_at),
            ]
        )

    return response


@role_required(User.Role.JOB_SEEKER)
def add_education(request):
    profile = JobSeekerProfile.objects.filter(user=request.user).first()

    if profile is None:
        messages.info(request, "Create your profile before adding education.")
        return redirect("accounts:edit_job_seeker_profile")

    form = EducationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        education = form.save(commit=False)
        education.profile = profile
        education.save()

        messages.success(request, "Education record added.")
        return redirect("accounts:job_seeker_area")

    return render(
        request,
        "accounts/education_form.html",
        {"form": form},
    )
