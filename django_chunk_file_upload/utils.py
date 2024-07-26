from __future__ import annotations

import hashlib
import os
from typing import Union

from django.conf import settings
from django.core.files.uploadedfile import (
    InMemoryUploadedFile,
    TemporaryUploadedFile,
)
from django.utils import timezone


def create_dir(dir_path: str) -> None:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def safe_remove_file(fp: str) -> None:
    try:
        os.remove(fp)
    except OSError:
        pass


def get_filename(fp: str) -> str:
    _, filename = os.path.split(fp)
    return filename


def get_file_extension(fp: str) -> str:
    _, extension = os.path.splitext(fp)
    return extension


def get_save_file_path(
    fp: str, upload_to: str = None, use_datetime: bool = True
) -> str:
    filename = get_filename(fp)
    media_root = str(settings.MEDIA_ROOT) if settings.MEDIA_ROOT else ""
    root_dir = os.path.join(
        media_root,
        (
            timezone.now().strftime(upload_to)
            if isinstance(upload_to, str)
            else timezone.now().strftime("%Y/%m/%d")
        ),
    )
    create_dir(root_dir)
    fp = os.path.join(root_dir, filename)
    return fp


def get_paths(
    fp: str, upload_to: str = "", use_datetime: bool = True
) -> tuple[str, str]:
    save_fp = get_save_file_path(fp, upload_to, use_datetime)
    media_root = str(settings.MEDIA_ROOT) if settings.MEDIA_ROOT else ""
    if media_root:
        fp = save_fp.split(media_root)[-1]
    else:
        fp = save_fp

    if fp[0] == "/":
        fp = fp[1:]

    return save_fp, fp


def get_file_path(
    filename: str, upload_dir: str = "", use_datetime: bool = True
) -> str:
    _save_fp, fp = get_paths(filename, upload_dir, use_datetime)
    return fp


def handle_upload_file(file, upload_dir: str = None, use_datetime: bool = True):
    save_fp, fp = get_paths(file.name, upload_dir, use_datetime)
    with open(save_fp, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
        return fp


def get_md5_checksum(
    fp: Union[str, InMemoryUploadedFile, TemporaryUploadedFile], chunk_size: int = 65536
) -> str:
    md5hash = hashlib.md5()
    if isinstance(fp, str):
        with open(fp, "rb") as fp:
            while chunk := fp.read(chunk_size):
                md5hash.update(chunk)
    else:
        for chunk in fp.chunks(chunk_size):
            md5hash.update(chunk)
    return md5hash.hexdigest()
