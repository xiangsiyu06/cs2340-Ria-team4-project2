from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("applications/", views.my_applications, name="my_applications"),
    path("<int:pk>/applications/", views.job_applications, name="job_applications"),
    path("applications/<int:pk>/", views.application_detail, name="application_detail"),
    path("applications/<int:pk>/status/", views.application_status, name="application_status"),
    path("new/", views.job_create, name="create"),
    path("mine/", views.my_jobs, name="mine"),
    path("<int:pk>/", views.job_detail, name="detail"),
    path("<int:pk>/apply/", views.job_apply, name="apply"),
    path("<int:pk>/edit/", views.job_edit, name="edit"),
    path("", views.job_search, name="search"),
    path("moderation/", views.moderation_list, name="moderation"),
    path("<int:pk>/remove/", views.job_remove, name="remove"),
    path("<int:pk>/restore/", views.job_restore, name="restore"),
]
