import re
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User
from .forms import ApplicationForm, JobForm
from .models import Application, Job
from django.db.models import Q
from .forms import JobForm, JobSearchForm


def recruiter_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.RECRUITER:
            return HttpResponseForbidden("Recruiters only.")
        return view_func(request, *args, **kwargs)
    return wrapper


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
    job = get_object_or_404(Job, pk=pk, status=Job.Status.ACTIVE)
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
