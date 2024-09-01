from __future__ import annotations

import hashlib
import json
import os
import shutil
from io import BufferedReader, BytesIO
from typing import Union
from uuid import UUID

from django.conf import settings
from django.core.files.uploadedfile import (
    InMemoryUploadedFile,
    TemporaryUploadedFile,
)
from django.utils import timezone


def _attr_to_str(*args, **kwargs) -> str:
    return ":".join([str(arg) for arg in args] + [json.dumps(kwargs, default=str)])


def make_md5_hash(*args, **kwargs) -> str:
    return hashlib.md5(_attr_to_str(*args, **kwargs).encode("utf-8")).hexdigest()


def make_uuid(*args, **kwargs) -> UUID:
    return UUID(hex=make_md5_hash(*args, **kwargs))


def remove_dir(dir_path: str) -> None:
    try:
        shutil.rmtree(dir_path)
    except OSError:
        pass


def create_dir(dir_path: str) -> None:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def get_dir(upload_to: str = None) -> str:
    media_root = str(settings.MEDIA_ROOT) if settings.MEDIA_ROOT else ""
    root_dir = os.path.join(
        media_root,
        (
            timezone.now().strftime(upload_to)
            if isinstance(upload_to, str)
            else timezone.now().strftime("%Y/%m/%d")
        ),
    )
    return root_dir


def safe_remove_file(fp: str) -> None:
    try:
        os.remove(fp)
    except OSError:
        pass


def get_filename(fp: str, remove_extension: bool = False) -> str:
    _, filename = os.path.split(fp)
    if remove_extension:
        filename = os.path.splitext(filename)[0]
    return filename


def get_file_extension(fp: str) -> str:
    _, extension = os.path.splitext(fp)
    return extension


def get_save_file_path(fp: str, upload_to: str = None) -> str:
    filename = get_filename(fp)
    root_dir = get_dir(upload_to)
    create_dir(root_dir)
    fp = os.path.join(root_dir, filename)
    return fp


def get_paths(fp: str, upload_to: str = "") -> tuple[str, str]:
    save_fp = get_save_file_path(fp, upload_to)
    media_root = str(settings.MEDIA_ROOT) if settings.MEDIA_ROOT else ""
    if media_root:
        fp = save_fp.split(media_root)[-1]
    else:
        fp = save_fp

    if fp[0] == "/":
        fp = fp[1:]

    return save_fp, fp


def get_file_path(filename: str, upload_dir: str = "") -> str:
    _save_fp, fp = get_paths(filename, upload_dir)
    return fp


def join_file_path(*args: str) -> str:
    return os.path.join(*args)


def handle_upload_file(file, upload_dir: str = None):
    save_fp, fp = get_paths(file.name, upload_dir)
    with open(save_fp, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
        return fp


def get_md5_checksum(
    fp: Union[str, bytes, BytesIO, InMemoryUploadedFile, TemporaryUploadedFile],
    chunk_size: int = 65536,
) -> str:
    md5hash = hashlib.md5()
    if isinstance(fp, str):
        with open(fp, "rb") as fp:
            while chunk := fp.read(chunk_size):
                md5hash.update(chunk)
    elif isinstance(fp, (InMemoryUploadedFile, TemporaryUploadedFile)):
        for chunk in fp.chunks(chunk_size):
            md5hash.update(chunk)
    elif isinstance(fp, BufferedReader):
        while chunk := fp.read(chunk_size):
            md5hash.update(chunk)
    else:
        fp = BytesIO(fp) if isinstance(fp, bytes) else fp
        with open(fp) as f:
            while chunk := f.read(chunk_size):
                md5hash.update(chunk)
    return md5hash.hexdigest()
