from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from .typed import StatusChoices


class FileManager(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(_("Name"), max_length=255)
    file = models.FileField()
    status = models.CharField(
        _("Status"),
        max_length=255,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    checksum = models.CharField(max_length=255, unique=True)
    eof = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = "django_chunk_file_upload"
        indexes = [models.Index(fields=["checksum"], name="file_manager_checksum_idx")]
        verbose_name = _("Django Chunk File Upload")
        verbose_name_plural = _("Django Chunk File Upload")

    def __str__(self):
        return self.name
