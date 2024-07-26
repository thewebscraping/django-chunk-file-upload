from __future__ import annotations

from django.urls import path

from .views import ChunkedUploadView


app_name = "django_chunk_file_upload"
urlpatterns = [
    path("uploads/", ChunkedUploadView.as_view(), name="uploads"),
]
