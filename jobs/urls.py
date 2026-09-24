from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("new/", views.job_create, name="create"),
    path("mine/", views.my_jobs, name="mine"),
    path("<int:pk>/", views.job_detail, name="detail"),
    path("<int:pk>/apply/", views.job_apply, name="apply"),
    path("<int:pk>/edit/", views.job_edit, name="edit"),
    path("", views.job_search, name="search"),
]
