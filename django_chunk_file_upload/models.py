from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import StatusChoices, TypeChoices


class FileManagerMixin(models.Model):
    """File Manager Mixin for Django Models"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.FileField()
    status = models.CharField(
        _("Status"),
        max_length=255,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    type = models.CharField(
        _("Type"),
        max_length=255,
        choices=TypeChoices.choices,
        default=TypeChoices.__empty__,
    )
    checksum = models.CharField(max_length=255)
    eof = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_files",
    )
    metadata = models.JSONField(default=dict)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @property
    def name(self) -> str:
        if "name" in self.metadata and self.metadata["name"]:
            return self.metadata["name"]
        return self.file.name


class FileManager(FileManagerMixin):
    """File Manager for Django Models"""

    class Meta:
        db_table = "django_chunk_file_upload"
        indexes = [models.Index(fields=["checksum"], name="%(class)s_checksum_idx")]
        ordering = ("-created_at",)
        unique_together = (
            "user",
            "checksum",
        )
        verbose_name = _("File Manager")
        verbose_name_plural = _("File Manager")
