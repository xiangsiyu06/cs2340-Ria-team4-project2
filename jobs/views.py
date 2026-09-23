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
