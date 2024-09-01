from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from re import match
from typing import Any, Union
from uuid import UUID

from django.core.files.uploadedfile import (
    InMemoryUploadedFile,
    TemporaryUploadedFile,
)
from django.utils.translation import gettext_lazy as _

from .constants import TypeChoices
from .optimize import MapOptimizer
from .utils import (
    get_file_extension,
    get_file_path,
    get_save_file_path,
    make_uuid,
)


@dataclass(kw_only=True)
class BaseFile:
    """Base File"""

    common_types = {
        TypeChoices.ARCHIVE: (
            ".bz",
            ".bz2",
            ".gz",
            ".jar",
            ".rar",
            ".tar",
            ".zip",
            ".7z",
        ),
        TypeChoices.AUDIO: (
            ".aac",
            ".mid",
            ".midi",
            ".mp3",
            ".oga",
            ".opus",
            ".wav",
            ".weba",
            ".3gp",
            ".3g2",
        ),
        TypeChoices.BINARY: (".bin",),
        TypeChoices.DOCUMENT: (
            ".abw",
            ".arc",
            ".odp",
            ".odt",
            ".pdf",
            ".md",
        ),
        TypeChoices.FONT: (
            ".eot",
            ".otf",
            ".ttf",
            ".woff",
            ".woff2",
        ),
        TypeChoices.HYPERTEXT: (
            ".html",
            ".HTM",
        ),
        TypeChoices.IMAGE: (
            ".apng",
            ".avif",
            ".bmp",
            ".gif",
            ".ico",
            ".jpeg",
            ".jpg",
            ".png",
            ".svg",
            ".tif",
            ".tiff",
            ".webp",
        ),
        TypeChoices.JSON: (
            ".json",
            ".jsonld",
        ),
        TypeChoices.MICROSOFT_WORD: (
            ".doc",
            ".docx",
        ),
        TypeChoices.MICROSOFT_POWERPOINT: (
            ".ppt",
            ".pptx",
        ),
        TypeChoices.MICROSOFT_EXCEL: (
            ".xls",
            ".xlsx",
        ),
        TypeChoices.SEPARATED: (
            ".csv",
            ".tsv",
        ),
        TypeChoices.TEXT: ("txt",),
        TypeChoices.VIDEO: (
            ".avi",
            ".mp4",
            ".mpeg",
            ".ogg",
            ".mp2t",
            ".webm",
            ".3gpp",
            ".3gpp2",
        ),
        TypeChoices.XML: ("xml",),
    }
    _accepted_mime_types: list = field(default_factory=lambda: [".*/*"])
    _id: UUID = None
    _user: Any = None
    _file: Any = None
    _type: TypeChoices = None
    _root_dir: str = None
    _path: str = None
    _extension: str = None
    _upload_to: str = None
    _message: str = None
    checksum: str = None
    chunk_from: str = None
    chunk_size: str = None
    chunk_to: str = None
    eof: bool = False
    mimetype: str = None
    name: str = None
    size: str = None

    @property
    def id(self) -> Any:
        if self._id is None:
            self._id = make_uuid(user=self.user, checksum=self.checksum)
        return self._id

    @property
    def file(self) -> Union[InMemoryUploadedFile, TemporaryUploadedFile, None]:
        return self._file

    @property
    def filename(self) -> None | str:
        if self.file:
            return getattr(self.file, "name", None)

    @property
    def repl_filename(self) -> str:
        return str(self.id)

    @property
    def user(self) -> Any:
        return self._user

    @property
    def path(self) -> str:
        if self._path is None:
            self._path = get_file_path(
                self.repl_filename + self.extension, self._upload_to
            )
        return self._path

    @path.setter
    def path(self, value: str) -> None:
        self._path = value

    @property
    def save_path(self) -> str:
        return get_save_file_path(self.path, self._upload_to)

    @property
    def extension(self) -> str:
        if self._extension is None and self.filename:
            self._extension = get_file_extension(self.filename)
        return self._extension

    @extension.setter
    def extension(self, value: str) -> None:
        self._extension = value

    @property
    def type(self) -> TypeChoices:
        if self._type is None:
            self._type = self._get_type(self.extension)
        return self._type

    @property
    def message(self) -> str:
        if self._message is None:
            self._message = _("Uploading file, please wait a moment.")
            if self.eof:
                self._message = _("File upload is completed.")
        return self._message

    @message.setter
    def message(self, value: str) -> None:
        self._message = value

    @classmethod
    def model_fields_set(cls) -> set:
        return {obj.name for obj in fields(cls)}

    @classmethod
    def from_request(cls, request, upload_to: str = "%Y/%m/%d") -> "File":
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
            X-File-MimeType: MINE type of file.

        Reference: django_chunk_file_upload/static/js/upload.chunk.js

        Args:
          request: AJAX request from client
          upload_to: Server upload dir.

        Returns:
          The File Metadata instance.
        """

        def to_private_attrs():
            user = None
            if request.user and request.user.is_authenticated:
                user = request.user

            file = request.FILES.get("file")
            pk = make_uuid(user=user, checksum=request.headers.get("x-file-checksum"))
            return {
                "_id": pk,
                "_extension": get_file_extension(file.name) if file else None,
                "_file": file,
                "_user": user,
                "_upload_to": upload_to,
            }

        kwargs = {}
        model_fields = {
            model_field
            for model_field in cls.model_fields_set()
            if not model_field.startswith("_")
        }

        for k, v in request.headers.items():
            if str(k).lower().startswith("x-file-"):
                param = str(k)[7:].replace("-", "_").lower()
                if param in model_fields:
                    if param == "eof":
                        v = bool(str(v).lower() in ["true", "1", "yes", "on"])

                    kwargs[param] = v

        kwargs.update(to_private_attrs())
        ret = cls(**kwargs)
        return ret

    def _get_type(self, extension: str) -> TypeChoices:
        for common_type, extensions in self.common_types.items():
            if str(extension).lower() in extensions:
                return common_type
        return TypeChoices.__empty__

    def is_valid(self) -> bool:
        if not (self.checksum and self.mimetype and self.file):
            return False

        for pattern in self._accepted_mime_types:
            if match(pattern, self.mimetype):
                return True

        return False

    def to_dict(self) -> dict:
        return asdict(self)

    def to_metadata(self) -> dict:
        return self.to_response().copy()

    def to_response(self) -> dict:
        metadata = {k: v for k, v in self.to_dict().items() if not k.startswith("_")}
        metadata["message"] = str(self.message)
        metadata["name"] = self.filename
        return metadata

    def write(self, mode: str = "ab+"):
        with open(self.save_path, mode) as fp:
            for chunk in self.file.chunks(self.chunk_size):
                fp.write(chunk)

    def optimize(self, instance):
        optimizer_class = MapOptimizer.get(self.type, None)
        if optimizer_class and isinstance(optimizer_class, type):
            optimizer = optimizer_class(instance, self)
            optimizer.run()


@dataclass(kw_only=True)
class File(BaseFile):
    """File"""

    _accepted_mime_types: list = field(default_factory=lambda: [".*/*"])


@dataclass(kw_only=True)
class AudioFile(File):
    """Audio File Metadata"""

    _accepted_mime_types: list = field(default_factory=lambda: [r"audio/*"])


@dataclass(kw_only=True)
class ArchiveFile(File):
    """Archive File"""

    _accepted_mime_types: list = field(
        default_factory=lambda: [
            r"application/x-bzip",
            r"application/x\-bzip2",
            r"application/gzip",
            r"application/x\-gzip",
            r"application/java\-archive",
            r"application/vnd\.rar",
            r"application/x\-tar",
            r"application/zip",
            r"x\-zip\-compressed",
            r"application/x\-7z\-compressed",
        ]
    )

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.ARCHIVE


@dataclass(kw_only=True)
class BinaryFile(File):
    """Binary File"""

    _accepted_mime_types: list = field(
        default_factory=lambda: [r"application/octet\-stream"]
    )

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.BINARY


@dataclass(kw_only=True)
class DocumentFile(File):
    """Document File Metadata"""

    _accepted_mime_types: list = field(
        default_factory=lambda: [
            r"application/x\-abiword",
            r"application/x\-freearc",
            r"application/msword",
            r"application/vnd\.openxmlformats\-officedocument\.wordprocessingml\.document",
            r"application/vnd\.oasis\.opendocument\.presentation",
            r"application/vnd\.oasis\.opendocument\.text",
            r"application/pdf",
            r"text/markdown",
        ]
    )

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.DOCUMENT


@dataclass(kw_only=True)
class FontFile(File):
    """Font File"""

    _accepted_mime_types: list = field(
        default_factory=lambda: [r"application/vnd\.ms\-fontobject", r"font/*"]
    )

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.FONT


@dataclass(kw_only=True)
class HyperTextFile(File):
    """HyperText Markup Language File Metadata"""

    _accepted_mime_types: list = field(default_factory=lambda: [r"text/html"])

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.HYPERTEXT


@dataclass(kw_only=True)
class ImageFile(File):
    """Image File"""

    _accepted_mime_types: list = field(default_factory=lambda: [r"image/*"])

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.IMAGE


@dataclass(kw_only=True)
class JSONFile(File):
    """JSON File"""

    _accepted_mime_types: list = field(
        default_factory=lambda: [r"application/json", r"application/ld\+json"]
    )

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.JSON


@dataclass(kw_only=True)
class MicrosoftWordFile(File):
    """Microsoft Word File"""

    _accepted_mime_types: list = field(
        default_factory=lambda: [
            r"application/msword",
            r"application/vnd\.openxmlformats\-officedocument\.wordprocessingml\.document",
        ]
    )

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.MICROSOFT_WORD


@dataclass(kw_only=True)
class MicrosoftPowerPointFile(File):
    """Microsoft PowerPoint File"""

    _accepted_mime_types: list = field(
        default_factory=lambda: [
            r"application/vnd\.ms\-powerpoint",
            r"application/vnd\.openxmlformats\-officedocument\.presentationml\.presentation",
        ]
    )

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.MICROSOFT_POWERPOINT


@dataclass(kw_only=True)
class MicrosoftExcelFile(File):
    """Microsoft Excel File"""

    _accepted_mime_types: list = field(
        default_factory=lambda: [
            r"application/vnd\.ms\-excel",
            r"application/vnd\.openxmlformats\-officedocument\.spreadsheetml\.sheet",
        ]
    )

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.MICROSOFT_EXCEL


@dataclass(kw_only=True)
class SeparatedFile(File):
    """Separated File"""

    _accepted_mime_types: list = field(default_factory=lambda: [r"text/csv"])

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.SEPARATED


@dataclass(kw_only=True)
class XMLFile(File):
    """XML File"""

    _accepted_mime_types: list = field(
        default_factory=lambda: [
            r"application/xml",
            r"text/xml",
            r"application/atom\+xml",
        ]
    )

    @property
    def type(self) -> TypeChoices:
        return TypeChoices.XML
