from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "registration-complete/",
        views.registration_complete,
        name="registration_complete",
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "job-seeker/",
        views.job_seeker_area,
        name="job_seeker_area",
    ),
    path(
        "recruiter/",
        views.recruiter_area,
        name="recruiter_area",
    ),
    path("reports/", views.reporting, name="reporting"),
    path(
        "reports/users.csv",
        views.export_users_csv,
        name="export_users_csv",
    ),
    path(
        "job-seeker/profile/",
        views.edit_job_seeker_profile,
        name="edit_job_seeker_profile",
    ),
]
