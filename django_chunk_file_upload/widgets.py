from __future__ import annotations

from django import forms

from .app_settings import app_settings


class DragDropFileInput(forms.ClearableFileInput):
    template_name = "django_chunk_file_upload/forms/widgets/file_input.html"

    @property
    def media(self):
        return forms.Media(
            css={"all": app_settings.css},
            js=app_settings.js,
        )


class DragDropFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", DragDropFileInput())
        super().__init__(*args, **kwargs)


class MultipleDragDropFileInput(DragDropFileInput):
    allow_multiple_selected = True


class MultipleDragDropFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleDragDropFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result
