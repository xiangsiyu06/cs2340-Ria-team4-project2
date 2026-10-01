from django.urls import path

from . import views

app_name = "communications"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("candidates/<int:candidate_pk>/", views.start_conversation, name="start"),
    path("<int:pk>/", views.conversation_detail, name="detail"),
]
