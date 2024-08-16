from __future__ import annotations

from dataclasses import dataclass, fields

from django.conf import settings

from .constants import StatusChoices
from .permissions import BasePermission, IsAuthenticated


@dataclass(kw_only=True)
class _Settings:

    @classmethod
    def get_kwargs(cls, **kwargs) -> dict:
        model_fields = {field.name for field in fields(cls)}
        return {k: v for k, v in kwargs.items() if k in model_fields}

    @classmethod
    def from_kwargs(cls, **kwargs) -> "_Settings":
        return cls(**cls.get_kwargs(**kwargs))


@dataclass(kw_only=True)
class _ImageSettings(_Settings):
    quality: int = 82
    compress_level: int = 9
    max_width: int = 1280
    max_height: int = 720
    to_webp: bool = True


@dataclass(kw_only=True)
class _LazySettings(_Settings):
    css: tuple | list | set = (
        "css/upload.chunk.css",
        "css/toastr.min.css",
        "css/sweetalert2.min.css",
    )
    js: tuple | list | set = (
        "js/jquery-3.7.1.min.js",
        "js/spark-md5.min.js",
        "js/toastr.min.js",
        "js/sweetalert2.min.js",
        "js/upload.chunk.js",
    )
    upload_to: str = "%Y/%m/%d"
    chunk_size: int = 1024 * 1024 * 2  # 2MB
    is_metadata_storage: bool = False
    remove_file_on_update: bool = True
    status: StatusChoices = StatusChoices.PENDING
    permission_classes: tuple[BasePermission] = (IsAuthenticated,)
    optimize: bool = True
    image_optimizer: _ImageSettings = _ImageSettings()

    @classmethod
    def from_kwargs(cls, **kwargs) -> "_LazySettings":
        kwargs = cls.get_kwargs(**kwargs)
        js = kwargs.pop("js", None) or []
        if js and isinstance(js, list):
            kwargs["js"] = list(set(js + ["js/upload.chunk.js"]))

        image_optimizer = kwargs.pop("image_optimizer", {}) or {}
        if image_optimizer and isinstance(image_optimizer, dict):
            kwargs["image_optimizer"] = _ImageSettings.from_kwargs(**image_optimizer)
        return cls(**kwargs)


app_settings = _LazySettings.from_kwargs(
    **getattr(settings, "DJANGO_CHUNK_FILE_UPLOAD", {})
)
