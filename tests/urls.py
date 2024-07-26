from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("file-manager/", include("django_chunk_file_upload.urls")),
]
