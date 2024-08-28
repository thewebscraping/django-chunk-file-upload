from __future__ import annotations

from django.contrib import admin

from .forms import ChunkedUploadFileAdminForm
from .models import FileManager


@admin.register(FileManager)
class FileManagerModelAdmin(admin.ModelAdmin):
    form = ChunkedUploadFileAdminForm
    list_display = (
        "id",
        "name",
        "status",
        "created_at",
        "updated_at",
    )

    add_form_template = "django_chunk_file_upload/admin/add_form.html"
    change_form_template = "django_chunk_file_upload/admin/change_form.html"
