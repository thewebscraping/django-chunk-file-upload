from __future__ import annotations

from django import forms

from .models import FileManager
from .widgets import DragDropFileField, MultipleDragDropFileField


class ChunkedUploadFileForm(forms.ModelForm):
    file = MultipleDragDropFileField(label="", required=True)

    class Meta:
        model = FileManager
        fields = ("file",)
        exclude = (
            "checksum",
            "eof",
            "status",
            "metadata",
        )


class ChunkedUploadFileAdminForm(ChunkedUploadFileForm):
    file = DragDropFileField()
