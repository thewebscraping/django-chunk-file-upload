from __future__ import annotations

from django import forms
from django.db.models.fields.files import FieldFile, ImageField

from .app_settings import app_settings


class DragDropFileInput(forms.ClearableFileInput):
    template_name = "django_chunk_file_upload/forms/widgets/drag_drop_input.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"]["required"] = False
        context["widget"]["attrs"]["hidden"] = True
        context["widget"]["attrs"]["data-id"] = "dropzone"
        if value and isinstance(value, (FieldFile, ImageField)):
            context["widget"]["attrs"]["data-value"] = value.instance.pk
        return context

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
