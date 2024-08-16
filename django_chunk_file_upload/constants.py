from __future__ import annotations

from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class TypeChoices(TextChoices):
    ARCHIVE = "ARCHIVE", _("ARCHIVE")
    AUDIO = "AUDIO", _("AUDIO")
    BINARY = "BINARY", _("BINARY")
    DOCUMENT = "DOCUMENT", _("DOCUMENT")
    FONT = "FONT", _("FONT")
    HYPERTEXT = "HYPERTEXT", _("HYPERTEXT")
    IMAGE = "IMAGE", _("IMAGE")
    JSON = "JSON", _("JSON")
    MICROSOFT_EXCEL = "MICROSOFT_EXCEL", _("MICROSOFT_EXCEL")
    MICROSOFT_POWERPOINT = "MICROSOFT_POWERPOINT", _("MICROSOFT_POWERPOINT")
    MICROSOFT_WORD = "MICROSOFT_WORD", _("MICROSOFT_WORD")
    SOURCE_CODE = "SOURCE_CODE", _("SOURCE_CODE")
    SEPARATED = "SEPARATED", _("SEPARATED")
    TEXT = "TEXT", _("TEXT")
    VIDEO = "VIDEO", _("VIDEO")
    XML = "XML", _("XML")
    __empty__ = _("Unknown")


class StatusChoices(TextChoices):
    COMPLETED = "COMPLETED", _("Completed")
    ERROR = "ERROR", _("Error")
    PENDING = "PENDING", _("Pending")
    PROCESSING = "PROCESSING", _("Processing")


class ActionChoices(TextChoices):
    CREATE = "_add", _("Add")
    UPDATE = "_save", _("Save")
    DELETE = "_delete", _("Delete")
