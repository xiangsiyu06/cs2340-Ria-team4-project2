from django.conf import settings
from django.db import models


class Job(models.Model):
    class RemoteType(models.TextChoices):
        REMOTE = "remote", "Remote"
        ON_SITE = "on_site", "On-site"
        HYBRID = "hybrid", "Hybrid"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        REMOVED = "removed", "Removed"

    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    address = models.CharField(max_length=300, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    remote_type = models.CharField(
        max_length=10,
        choices=RemoteType.choices,
        default=RemoteType.ON_SITE,
    )
    visa_sponsorship = models.BooleanField(default=False)
    skills = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated, e.g. Python, Django, SQL",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.company}"

    def skill_list(self):
        return [s.strip() for s in self.skills.split(",") if s.strip()]


class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    note = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "applicant"], name="unique_job_application"
            ),
        ]

    def __str__(self):
        return f"{self.applicant} applied to {self.job}"
