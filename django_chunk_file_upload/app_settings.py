from __future__ import annotations

import importlib
from dataclasses import dataclass, field, fields

from django.conf import settings

from . import permissions
from .constants import StatusChoices


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
    remove_origin: bool = True


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
    permission_classes: tuple[permissions.BasePermission] = (
        permissions.IsAuthenticated,
    )
    optimize: bool = True
    image_optimizer: _ImageSettings = field(default_factory=_ImageSettings)

    @classmethod
    def from_kwargs(cls, **kwargs) -> "_LazySettings":
        kwargs = cls.get_kwargs(**kwargs)
        js = kwargs.pop("js", None) or []
        if js and isinstance(js, list):
            kwargs["js"] = list(set(js + ["js/upload.chunk.js"]))

        image_optimizer = kwargs.pop("image_optimizer", {}) or {}
        if image_optimizer and isinstance(image_optimizer, dict):
            kwargs["image_optimizer"] = _ImageSettings.from_kwargs(**image_optimizer)

        permission_classes = kwargs.pop("permission_classes", None)
        if permission_classes and isinstance(
            permission_classes, (tuple, list, set, str)
        ):
            if isinstance(permission_classes, str):
                permission_classes = [permission_classes]

            perms = []
            for permission_class in permission_classes:
                paths = permission_class.split(".")
                module = importlib.import_module(".".join(paths[:-1]), "")
                permission_class = getattr(module, paths[-1])
                perms.append(permission_class)

            kwargs["permission_classes"] = tuple(perms)
        return cls(**kwargs)


app_settings = _LazySettings.from_kwargs(
    **getattr(settings, "DJANGO_CHUNK_FILE_UPLOAD", {})
)
