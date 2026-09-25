import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import JobSeekerProfile, User
from .forms import ApplicationForm, ApplicationStatusForm, JobForm, JobSearchForm
from .models import Application, Job

recruiter_required = role_required(User.Role.RECRUITER)
admin_required = role_required(User.Role.ADMINISTRATOR)


@role_required(User.Role.JOB_SEEKER)
def my_applications(request):
    applications = (
        Application.objects.filter(applicant=request.user)
        .select_related("job")
        .order_by("-created_at", "-pk")
    )
    return render(request, "jobs/my_applications.html", {"applications": applications})


@recruiter_required
def job_applications(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    applications = job.applications.select_related("applicant").order_by("-created_at", "-pk")
    return render(request, "jobs/job_applications.html", {
        "job": job, "applications": applications,
    })


def _application_review_context(application, status_form):
    profile = (
        JobSeekerProfile.objects.filter(user=application.applicant)
        .prefetch_related("education_records", "work_experiences", "professional_links")
        .first()
    )
    return {"application": application, "profile": profile, "status_form": status_form}


@recruiter_required
def application_detail(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("job", "applicant"),
        pk=pk, job__recruiter=request.user,
    )
    return render(request, "jobs/application_detail.html", _application_review_context(
        application, ApplicationStatusForm(instance=application),
    ))


@recruiter_required
@require_POST
def application_status(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("job", "applicant"),
        pk=pk, job__recruiter=request.user,
    )
    form = ApplicationStatusForm(request.POST, instance=application)
    if form.is_valid():
        # Only update the stage; never overwrite the applicant's submitted note.
        application.status = form.cleaned_data["status"]
        application.save(update_fields=["status"])
        messages.success(request, "Application status updated.")
        return redirect("jobs:application_detail", pk=application.pk)
    return render(request, "jobs/application_detail.html", _application_review_context(
        application, form,
    ))


@recruiter_required
def job_create(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.save()
            return redirect("jobs:detail", pk=job.pk)
    else:
        form = JobForm()
    return render(request, "jobs/job_form.html", {"form": form, "job": None})


@recruiter_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect("jobs:detail", pk=job.pk)
    else:
        form = JobForm(instance=job)
    return render(request, "jobs/job_form.html", {"form": form, "job": job})


@recruiter_required
def my_jobs(request):
    jobs = request.user.jobs.all()
    return render(request, "jobs/my_jobs.html", {"jobs": jobs})


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if job.status == Job.Status.REMOVED:
        user = request.user
        can_see = user.is_authenticated and (
            user == job.recruiter or user.role == User.Role.ADMINISTRATOR
        )
        if not can_see:
            raise Http404

    application = None
    if request.user.is_authenticated and request.user.role == User.Role.JOB_SEEKER:
        application = Application.objects.filter(job=job, applicant=request.user).first()
    return render(request, "jobs/job_detail.html", {
        "job": job,
        "application": application,
        "application_form": ApplicationForm(),
    })


@role_required(User.Role.JOB_SEEKER)
@require_POST
def job_apply(request, pk):
    job = get_object_or_404(Job, pk=pk, status=Job.Status.ACTIVE)
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, "You have already applied to this job.")
        return redirect("jobs:detail", pk=job.pk)

    form = ApplicationForm(request.POST)
    if not form.is_valid():
        return render(request, "jobs/job_detail.html", {
            "job": job,
            "application_form": form,
        })

    # The database constraint also protects against simultaneous submissions.
    application, created = Application.objects.get_or_create(
        job=job, applicant=request.user, defaults={"note": form.cleaned_data["note"]}
    )
    if created:
        messages.success(request, "Your application has been submitted.")
    else:
        messages.info(request, "You have already applied to this job.")
    return redirect("jobs:detail", pk=job.pk)

@login_required
def job_search(request):
    form = JobSearchForm(request.GET or None)
    jobs = Job.objects.filter(status=Job.Status.ACTIVE)

    if form.is_valid():
        data = form.cleaned_data

        if data["title"]:
            jobs = jobs.filter(title__icontains=data["title"])

        for skill in data["skills"].split(","):
            skill = skill.strip()
            if skill:
                pattern = r"(^|,)\s*" + re.escape(skill) + r"\s*(,|$)"
                jobs = jobs.filter(skills__iregex=pattern)

        if data["location"]:
            jobs = jobs.filter(address__icontains=data["location"])

        lo, hi = data["salary_min"], data["salary_max"]
        if lo is not None:
            jobs = jobs.filter(
                Q(salary_max__gte=lo) | Q(salary_max__isnull=True, salary_min__isnull=False)
            )
        if hi is not None:
            jobs = jobs.filter(
                Q(salary_min__lte=hi) | Q(salary_min__isnull=True, salary_max__isnull=False)
            )

        if data["remote_type"]:
            jobs = jobs.filter(remote_type=data["remote_type"])

        if data["visa_sponsorship"]:
            jobs = jobs.filter(visa_sponsorship=True)

    elif form.is_bound:
        jobs = jobs.none()
    return render(request, "jobs/job_search.html", {"form": form, "jobs": jobs})


@admin_required
def moderation_list(request):
    status = request.GET.get("status", "")
    jobs = Job.objects.select_related("recruiter")
    if status in Job.Status.values:
        jobs = jobs.filter(status=status)
    return render(request, "jobs/moderation.html", {"jobs": jobs, "status": status})


@require_POST
@admin_required
def job_remove(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.status = Job.Status.REMOVED
    job.save(update_fields=["status"])
    messages.success(request, f'Removed "{job.title}".')
    return redirect("jobs:moderation")


@require_POST
@admin_required
def job_restore(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.status = Job.Status.ACTIVE
    job.save(update_fields=["status"])
    messages.success(request, f'Restored "{job.title}".')
    return redirect("jobs:moderation")
