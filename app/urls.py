from django.urls import path
from app import views

app_name = "app"

urlpatterns = [
    path("callback/", views.CallbackView.as_view(), name="callback"),
    path("youtube/", views.YouTubeView.as_view(), name="youtube"),
]
