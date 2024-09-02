from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoChunkFileUploadConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_chunk_file_upload"
    verbose_name = _("Django Files")
