from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from accounts.decorators import role_required
from accounts.models import User
from jobs.models import Job
from .forms import ReportForm, ReportReviewForm
from .models import Report

admin_required = role_required(User.Role.ADMINISTRATOR)


def _submit(request, target, target_type):
    form = ReportForm(request.POST if request.method == "POST" else None)
    label = str(target)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.target_type = target_type
        report.target_label = label
        if target_type == Report.TargetType.JOB:
            report.reported_job = target
            report.target_snapshot = (
                f"Title: {target.title}\nCompany: {target.company}\n"
                f"Recruiter: {target.recruiter.username}\nAddress: {target.address}\n"
                f"Work type: {target.get_remote_type_display()}\n"
                f"Salary: {target.salary_min if target.salary_min is not None else 'Not provided'} - "
                f"{target.salary_max if target.salary_max is not None else 'Not provided'}\n"
                f"Visa sponsorship: {'Available' if target.visa_sponsorship else 'Not offered'}\n"
                f"Skills: {target.skills}\n\n{target.description}"
            )
        else:
            report.reported_user = target
            report.target_snapshot = f"Username: {target.username}\nRole: {target.get_role_display()}"
        report.save()
        messages.success(request, "Your report has been submitted for administrator review.")
        return redirect("reports:submitted")
    return render(request, "reports/submit.html", {
        "form": form, "target_label": label, "target_type": target_type,
    })


@login_required
@require_http_methods(["GET", "POST"])
def report_job(request, pk):
    job = get_object_or_404(Job.objects.select_related("recruiter"), pk=pk, status=Job.Status.ACTIVE)
    return _submit(request, job, Report.TargetType.JOB)


@login_required
@require_http_methods(["GET", "POST"])
def report_user(request, pk):
    user = get_object_or_404(User, pk=pk, is_active=True)
    if user == request.user:
        raise PermissionDenied("You cannot report your own account.")
    return _submit(request, user, Report.TargetType.USER)


@login_required
@require_GET
def submitted(request):
    return render(request, "reports/submitted.html")


@admin_required
@require_GET
def report_list(request):
    reports = Report.objects.select_related("reporter")
    status = request.GET.get("status", "")
    target_type = request.GET.get("type", "")
    query = request.GET.get("q", "").strip()
    if status in Report.Status.values:
        reports = reports.filter(status=status)
    if target_type in Report.TargetType.values:
        reports = reports.filter(target_type=target_type)
    if query:
        reports = reports.filter(Q(target_label__icontains=query) | Q(details__icontains=query))
    page = Paginator(reports, 25).get_page(request.GET.get("page"))
    return render(request, "reports/list.html", {
        "page_obj": page, "statuses": Report.Status.choices,
        "types": Report.TargetType.choices, "selected_status": status,
        "selected_type": target_type, "query": query,
    })


@admin_required
@require_http_methods(["GET", "POST"])
def report_detail(request, pk):
    report = get_object_or_404(
        Report.objects.select_related("reporter", "reported_job", "reported_user", "reviewed_by"), pk=pk,
    )
    form = ReportReviewForm(request.POST if request.method == "POST" else None, instance=report)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.reviewed_by = request.user
        report.reviewed_at = timezone.now()
        report.save(update_fields=["status", "review_notes", "reviewed_by", "reviewed_at"])
        messages.success(request, "Report review saved.")
        return redirect("reports:detail", pk=report.pk)
    return render(request, "reports/detail.html", {"report": report, "form": form})
