from __future__ import annotations

from django.db import IntegrityError
from django.db.models import ManyToManyField, QuerySet
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from .app_settings import app_settings
from .forms import ChunkedUploadFileForm
from .models import FileManager
from .typed import FileMetadata, StatusChoices
from .utils import get_md5_checksum, safe_remove_file


class ChunkedUploadView(FormView):
    """Chunked upload view."""

    allowed_methods = ("POST",)
    template_name = "django_chunk_file_upload/chunked_upload.html"
    form_class = ChunkedUploadFileForm
    chunk_size = app_settings.chunk_size
    upload_to = app_settings.upload_to

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chunk_size"] = self.chunk_size
        return context

    def post(self, request, *args, **kwargs):
        """Override post method from FormView."""

        file_obj = FileMetadata.from_request(self.request, self.upload_to)
        form = self.get_form(self.form_class)
        # TOTO: Implement change view with replace image on admin.
        # action = self.request.POST.get("action", ActionChoices.ADD)
        if file_obj.is_valid() and form.is_valid():
            return self.chunked_upload(form, file_obj)

        file_obj.message = _("Invalid form.")
        return self.ajax_response(None, file_obj, status=400, commit=False)

    def chunked_upload(self, form, file_obj):
        """Chunked upload file

        Handle requests from JQuery AJAX, save files to server.
        Check MD5 checksum of file when upload is complete, if not correct delete file from server.

        Args:
            form (ChunkedUploadFileForm): Chunked upload from.
            file_obj (FileMetadata): File metadata instance.

        Returns:
            JsonResponse: return file metadata data.
        """

        instance = form.Meta.model.objects.filter(checksum=file_obj.checksum).first()
        if instance:
            mode = "ab+"
            if instance.eof:
                file_obj.message = _("The file already exists.")
                return self.ajax_response(instance, file_obj, 403, commit=False)

        else:
            mode = "wb+"
            instance = form.instance

        kwargs, m2m_kwargs = self.get_kwargs(form)
        for k, v in kwargs.items():
            setattr(instance, k, v)

        try:
            self.save(instance, file_obj)
            self.save_m2m(instance, **m2m_kwargs)
            file_obj.write(mode=mode)
        except Exception as e:
            return self.raise_exception(e, instance, file_obj)

        if file_obj.eof is False:
            return self.ajax_response(instance, file_obj)

        checksum = get_md5_checksum(file_obj.save_path)
        if checksum != file_obj.checksum:
            safe_remove_file(file_obj.save_path)
            instance.eof = False
            file_obj.message = _("The file does not match the MD5 checksum.")
            return self.ajax_response(instance, file_obj, 400)

        self.background_task(instance)
        return self.ajax_response(instance, file_obj)

    def raise_exception(
        self, exception: Exception, instance: FileManager, file_obj: FileMetadata
    ):
        if isinstance(exception, IntegrityError):
            file_obj.message = _("DB error: %s.") % str(exception)
        else:
            file_obj.message = str(exception)

        return self.ajax_response(instance, file_obj, 400)

    def ajax_response(
        self,
        instance: FileManager,
        file_obj: FileMetadata,
        status: int = 201,
        commit: bool = True,
    ):
        if commit:
            self.save(instance, file_obj)

        return JsonResponse(
            data=file_obj.to_dict(),
            status=status,
        )

    def get_kwargs(self, form, **kwargs) -> tuple[dict, dict]:
        kwargs, m2m_kwargs = {}, {}
        m2m_field = {
            field.attname: []
            for field in form.instance._meta.get_fields()
            if isinstance(field, ManyToManyField)
        }
        for k, v in form.cleaned_data.items():
            if k in m2m_field:
                m2m_kwargs[k] = v
            else:
                kwargs[k] = v
        return kwargs, m2m_kwargs

    def save_m2m(self, instance, **kwargs):
        for field, values in kwargs.items():
            m2m_field = getattr(instance, field, None)
            if m2m_field:
                if isinstance(values, QuerySet):
                    removed = []
                    added = {obj.id: obj for obj in values}
                    for obj in m2m_field.all():
                        if obj.id not in added:
                            removed.append(obj)
                        else:
                            added.pop(obj.id, None)

                    m2m_field.add(*added.values())
                    m2m_field.remove(*removed)
                else:
                    m2m_field.clear()

    def save(self, instance: FileManager, file_obj: FileMetadata):
        instance.eof = file_obj.eof
        instance.file = file_obj.path
        instance.status = (
            StatusChoices.COMPLETED if file_obj.eof else StatusChoices.PROCESSING
        )
        if not instance.checksum:
            instance.checksum = file_obj.checksum

        if not instance.name:
            instance.name = file_obj.name

        if app_settings.is_metadata_storage:
            instance.metadata = file_obj.to_dict()

        instance.save()

    def background_task(self, instance):
        pass
