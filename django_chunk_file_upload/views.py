from __future__ import annotations

from django.db import IntegrityError
from django.db.models import ManyToManyField, QuerySet
from django.http import Http404, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from .app_settings import app_settings
from .constants import ActionChoices
from .forms import ChunkedUploadFileForm
from .models import FileManager
from .typed import (
    ArchiveFile,
    AudioFile,
    BinaryFile,
    DocumentFile,
    File,
    FontFile,
    HyperTextFile,
    ImageFile,
    JSONFile,
    MicrosoftExcelFile,
    MicrosoftPowerPointFile,
    MicrosoftWordFile,
    SeparatedFile,
    XMLFile,
)
from .utils import get_md5_checksum


class ChunkedUploadView(FormView):
    """Chunked upload view."""

    http_method_names = ["get", "post", "delete"]
    chunk_size = app_settings.chunk_size
    file_class = File
    file_status = app_settings.status
    form_class = ChunkedUploadFileForm
    optimize = app_settings.optimize
    permission_classes = app_settings.permission_classes
    remove_file_on_update = app_settings.remove_file_on_update
    template_name = "django_chunk_file_upload/chunked_upload.html"
    upload_to = app_settings.upload_to

    def check_object_permissions(self, request):
        for permission in self.permission_classes:
            permission = permission() if isinstance(permission, type) else permission
            if permission.has_permission(request, self):
                return True
        return False

    def has_add_permission(self, request, obj=None) -> bool:
        return self.check_object_permissions(request)

    def has_view_permission(self, request, obj=None) -> bool:
        return self.check_object_permissions(request)

    def has_change_permission(self, request, obj=None) -> bool:
        return self.check_object_permissions(request)

    def has_delete_permission(self, request, obj=None) -> bool:
        return self.check_object_permissions(request)

    def is_valid(self, form, file_obj) -> bool:
        if form.is_valid() and file_obj.is_valid():
            return True
        return False

    def get_model(self):
        return self.form_class.Meta.model

    def get_instance(self):
        opts = dict(
            user=self.request.user if self.request.user.is_authenticated else None
        )
        pk = self.request.headers.get("x-file-id")
        if pk:
            opts["pk"] = pk
            return self.get_model().objects.filter(**opts).first()

        if self.request.headers.get("x-file-checksum"):
            opts["checksum"] = self.request.headers["x-file-checksum"]
            return self.get_model().objects.filter(**opts).first()

    def get_context_data(self, **kwargs):
        context = super(ChunkedUploadView, self).get_context_data(**kwargs)
        context["chunk_size"] = self.chunk_size
        return context

    def get(self, request, *args, **kwargs):
        return self._get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Override POST method from View."""

        action = request.POST.get("action")
        if action == ActionChoices.UPDATE:
            return self._update(request, *args, **kwargs)
        return self._post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Override DELETE method from View."""

        return self._delete(request, *args, **kwargs)

    def _get(self, request, *args, **kwargs):
        if self.has_view_permission(request):
            return super(ChunkedUploadView, self).get(request, *args, **kwargs)
        raise Http404

    def _post(self, request, *args, **kwargs):
        form, file_obj = self._get_form_file(request, *args, **kwargs)
        if self.has_add_permission(self.request) and self.is_valid(form, file_obj):
            instance = self.get_instance()
            return self.chunked_upload(instance, form, file_obj)

        file_obj.message = _("Permission denied.")
        return self.ajax_response(None, file_obj, status=400, save=False)

    def _update(self, request, *args, **kwargs):
        form, file_obj = self._get_form_file(request, *args, **kwargs)
        if self.has_change_permission(self.request) and self.is_valid(form, file_obj):
            instance = self.get_instance()
            if instance:
                if self.remove_file_on_update:
                    instance.file.delete()
                instance.eof = False
                instance.save()
                return self.chunked_upload(instance, form, file_obj)

            file_obj.message = _("Not found.")
            return self.ajax_response(None, file_obj, status=400, save=False)

        file_obj.message = _("Permission denied.")
        return self.ajax_response(None, file_obj, status=400, save=False)

    def _delete(self, request, *args, **kwargs):
        form, file_obj = self._get_form_file(request, *args, **kwargs)
        if self.has_delete_permission(request):
            instance = self.get_instance()
            if instance and (
                self.request.user.is_superuser or self.request.user == instance.user
            ):
                instance.file.delete()
                instance.delete()
                file_obj.message = _("The file deleted successfully.")
                return self.ajax_response(None, file_obj, status=200, save=False)

        file_obj.message = _("Permission denied.")
        return self.ajax_response(None, file_obj, status=400, save=False)

    def _get_form_file(
        self, request, *args, **kwargs
    ) -> tuple[ChunkedUploadFileForm, File]:
        form = self.get_form(self.form_class)
        file_obj = self.file_class.from_request(self.request, self.upload_to)
        return form, file_obj

    def chunked_upload(self, instance, form, file_obj):
        """Chunked upload file

        Handle requests from JQuery AJAX, save files to server.
        Check MD5 checksum of file when upload is complete, if not correct delete file from server.

        Args:
            instance (FileManager): FileManager object.
            form (ChunkedUploadFileForm): Chunked upload from.
            file_obj (File): File metadata instance.

        Returns:
            JsonResponse: return file metadata data.
        """
        if not instance:
            instance = form.instance

        if instance.eof:
            file_obj.message = _("The file already exists.")
            return self.ajax_response(instance, file_obj, 403, save=False)

        kwargs, m2m_kwargs = self.get_kwargs(form)
        for k, v in kwargs.items():
            setattr(instance, k, v)

        try:
            self.save(instance, file_obj)
            self.save_m2m(instance, **m2m_kwargs)
            file_obj.write("ab+" if instance.file else "wb+")
        except IntegrityError as e:
            return self.raise_exception(e, instance, file_obj)

        except Exception as e:
            return self.raise_exception(e, instance, file_obj)

        if file_obj.eof is False:
            return self.ajax_response(instance, file_obj)

        checksum = get_md5_checksum(file_obj.save_path)
        if checksum != file_obj.checksum:
            instance.file.delete()
            instance.eof = False
            file_obj.message = _("The file does not match the MD5 checksum.")
            return self.ajax_response(instance, file_obj, 400)

        self.background_task(instance)
        if self.optimize:
            file_obj.optimize(instance)
        return self.ajax_response(instance, file_obj)

    def raise_exception(
        self, exception: Exception, instance: FileManager, file_obj: File
    ):
        error = str(exception)
        file_obj.message = error
        if isinstance(exception, IntegrityError):
            file_obj.message = _("DB error: %s.") % error
            if "UNIQUE" in error:
                file_obj.message = _("The file was created by another user.")

            return self.ajax_response(instance, file_obj, 400, False)

        return self.ajax_response(instance, file_obj, 400)

    def ajax_response(
        self,
        instance: FileManager,
        file_obj: File,
        status: int = 201,
        save: bool = True,
    ):
        if save:
            self.save(instance, file_obj)

        data = file_obj.to_response()
        if instance and instance.eof:
            data["url"] = instance.file.url

        return JsonResponse(
            data=data,
            status=status,
        )

    def get_kwargs(self, form, **kwargs) -> tuple[dict, dict]:
        kwargs, m2m_kwargs = {}, {}
        m2m_field = {
            field.attname: []
            for field in form.instance._meta.get_fields()
            if isinstance(field, ManyToManyField)
        }
        if hasattr(form, "cleaned_data"):
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

    def save(self, instance: FileManager, file_obj: File):
        instance.eof = file_obj.eof
        instance.file = file_obj.path
        instance.type = file_obj.type
        instance.user = file_obj.user
        instance.status = self.file_status
        if not instance.checksum:
            instance.checksum = file_obj.checksum

        if app_settings.is_metadata_storage:
            instance.metadata = file_obj.to_metadata()

        instance.save()

    def background_task(self, instance):
        pass


class ChunkArchiveUploadView(ChunkedUploadView):
    """Chunk Archive Upload View"""

    file_class = ArchiveFile


class ChunkAudioUploadView(ChunkedUploadView):
    """Chunk Audio Upload View"""

    file_class = AudioFile


class ChunkBinaryUploadView(ChunkedUploadView):
    """Chunk Binary Upload View"""

    file_class = BinaryFile


class ChunkDocumentUploadView(ChunkedUploadView):
    """Chunk Document Upload View"""

    file_class = DocumentFile


class ChunkFontUploadView(ChunkedUploadView):
    """Chunk Font Upload View"""

    file_class = FontFile


class ChunkHyperTextUploadView(ChunkedUploadView):
    """Chunk HyperText Upload View"""

    file_class = HyperTextFile


class ChunkImageUploadView(ChunkedUploadView):
    """Chunk Image Upload View"""

    file_class = ImageFile


class ChunkJSONUploadView(ChunkedUploadView):
    """Chunk JSON Upload View"""

    file_class = JSONFile


class ChunkMicrosoftWordUploadView(ChunkedUploadView):
    """Chunk Microsoft Word Upload View"""

    file_class = MicrosoftWordFile


class ChunkMicrosoftPowerPointUploadView(ChunkedUploadView):
    """Chunk Microsoft PowerPoint Upload View"""

    file_class = MicrosoftPowerPointFile


class ChunkMicrosoftExcelUploadView(ChunkedUploadView):
    """Chunk Microsoft Excel Upload View"""

    file_class = MicrosoftExcelFile


class ChunkSeparatedUploadView(ChunkedUploadView):
    """Chunk Separated Upload View"""

    file_class = SeparatedFile


class ChunkXMLUploadView(ChunkedUploadView):
    """Chunk XML Upload View"""

    file_class = XMLFile
