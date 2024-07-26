from __future__ import annotations

from dataclasses import dataclass, field, fields
from re import match
from typing import Any, Union
from uuid import UUID

from django.core.files.uploadedfile import (
    InMemoryUploadedFile,
    TemporaryUploadedFile,
)
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from .utils import get_file_extension, get_paths


class StatusChoices(TextChoices):
    COMPLETED = "COMPLETED", _("Completed")
    ERROR = "ERROR", _("Error")
    PENDING = "PENDING", _("Pending")
    PROCESSING = "PROCESSING", _("Processing")


class ActionChoices(TextChoices):
    ADD = "_add", _("Add")
    SAVE = "_save", _("Save")
    DELETE = "_delete", _("Delete")


@dataclass(kw_only=True)
class FileMetadata:
    """File Metadata"""

    _accepted_mime_types: list = field(default_factory=lambda: [".*/*"])
    _id: UUID = None
    _file: Any = None
    _path: str = None
    _save_path: str = None
    _message: str = None
    checksum: str = None
    chunk_from: int = None
    chunk_size: int = None
    chunk_to: int = None
    eof: bool = False
    mime_type: str = None
    name: str = False
    size: str = False

    @property
    def id(self) -> UUID:
        if self._id is None and self.checksum:
            self._id = UUID(hex=self.checksum, version=4)
        return self._id

    @property
    def file(self) -> Union[InMemoryUploadedFile, TemporaryUploadedFile, None]:
        return self._file

    @property
    def path(self) -> str:
        return self._path

    @property
    def save_path(self) -> str:
        return self._save_path

    @property
    def message(self) -> str:
        if self._message is None:
            self._message = "Uploading file, please wait a moment."
            if self.eof:
                self._message = "File upload is completed."
        return self._message

    @message.setter
    def message(self, value: str) -> None:
        self._message = value

    @classmethod
    def from_request(cls, request, upload_to: str = "%Y/%m/%d") -> "FileMetadata":
        """Create instance from request

        Receive requests from the client using jQuery AJAX Method.
        We receive parameters using request headers, including::
            X-File-Name: File name
            X-File-Checksum: File MD5 checksum
            X-File-Chunk-From: Chunk from of File.
            X-File-Chunk-To: Chunk to of File.
            X-File-Chunk-Size: Chunk size per request.
            X-File-EOF: True is upload completed, otherwise.
            X-File-Size: Original file size.
            X-File-Mime-Type: MINE type of file.

        Reference: django_chunk_file_upload/static/js/upload.chunk.js

        Args:
          request: AJAX request from client
          upload_to: Server upload dir.

        Returns:
          The File Metadata instance.
        """
        kwargs = {}
        dataclass_fields = {
            field.name: field for field in fields(cls) if not field.name.startswith("_")
        }
        for k, v in request.headers.items():
            if str(k).lower().startswith("x-file-"):
                param = str(k)[7:].replace("-", "_").lower()
                if param in dataclass_fields:
                    kwargs[param] = v

        ret = cls(**kwargs)
        ret.eof = bool(str(ret.eof).lower() in ["true", "1", "yes", "on"])
        file = request.FILES.get("file")
        if file:
            ret._file = file
            ret._save_path, ret._path = get_paths(
                str(ret.id) + get_file_extension(ret.file.name), upload_to
            )
        return ret

    def is_valid(self) -> bool:
        if not (self.checksum and self.mime_type and self.file):
            return False

        for pattern in self._accepted_mime_types:
            if match(pattern, self.mime_type):
                return True

        return False

    def to_dict(self) -> dict:
        data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        data["message"] = self.message
        return data

    def write(self, mode: str = "ab+"):
        with open(self.save_path, mode) as fp:
            for chunk in self.file.chunks(self.chunk_size):
                fp.write(chunk)


@dataclass(kw_only=True)
class ImageFileMetadata(FileMetadata):
    """Image File Metadata"""

    _accepted_mime_types: list = field(default_factory=lambda: ["image/*"])


@dataclass(kw_only=True)
class CSVFileMetadata(FileMetadata):
    """CSV File Metadata"""

    _accepted_mime_types: list = field(default_factory=lambda: ["text/csv"])
