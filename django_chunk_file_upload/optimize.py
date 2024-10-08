from __future__ import annotations

from io import BufferedReader, BytesIO
from typing import TYPE_CHECKING, Union
from uuid import UUID

from django.db.models.fields.files import FieldFile, ImageFieldFile

from PIL import Image, UnidentifiedImageError
from PIL.JpegImagePlugin import JpegImageFile
from PIL.PngImagePlugin import PngImageFile
from PIL.WebPImagePlugin import WebPImageFile

from .app_settings import app_settings
from .constants import TypeChoices
from .utils import get_logger, get_md5_checksum, get_paths, safe_remove_file


if TYPE_CHECKING:
    from .models import FileManager
    from .typed import File

LOGGER = get_logger(__name__)

_File = Union[str | bytes | BytesIO | BufferedReader | FieldFile | ImageFieldFile]
_Image = Union[JpegImageFile, PngImageFile, WebPImageFile]
_ImageFile = Union[_File, _Image]


class BaseOptimizer:
    """Base Optimizer"""

    def __init__(self, instance: FileManager, file: File, *args, **kwargs):
        self._instance = instance
        self._file = file

    @property
    def instance(self) -> FileManager:
        return self._instance

    @property
    def file(self) -> File:
        return self._file

    @classmethod
    def open(cls, fp: _File) -> None | BufferedReader | BytesIO:
        return cls._open(fp)

    @classmethod
    def _open(cls, fp: _File) -> None | BufferedReader | BytesIO:
        if isinstance(fp, _File):
            if isinstance(fp, str):
                return open(fp, "rb")
            if isinstance(fp, bytes):
                fp = BytesIO(fp)
            if isinstance(fp, (BytesIO, BufferedReader)):
                return fp
            return fp.file.file

    @classmethod
    def close(cls, fp: _File) -> None:
        if isinstance(fp, (FieldFile, ImageFieldFile)):
            fp.close()
        else:
            if (
                fp
                and getattr(fp, "close", None)
                and bool(getattr(fp, "closed", None) is False)
            ):
                fp.close()

    @classmethod
    def checksum(cls, fp: _File):
        return get_md5_checksum(fp)

    @classmethod
    def get_identifier(cls, fp: _File) -> UUID:
        return UUID(hex=cls.checksum(fp))

    def run(self):
        pass


class ImageOptimizer(BaseOptimizer):
    """Image Optimizer"""

    _supported_file_types = (".jpg", ".jpeg", ".png", ".webp")

    def __init__(
        self,
        instance,
        file,
        *args,
        **kwargs,
    ):
        super().__init__(instance, file, *args, **kwargs)

    def run(self):
        image, path = self.optimize(self.file.save_path, upload_to=self.file._upload_to)
        self.file.path = path
        self.close(image)

    @classmethod
    def open(cls, fp: _File) -> None | Image.Image:
        try:
            if isinstance(fp, _Image):
                return fp

            image = Image.open(cls._open(fp))
            return image
        except (UnidentifiedImageError, FileNotFoundError):
            pass

    @classmethod
    def close(cls, fp: _ImageFile) -> None:
        if isinstance(fp, (Image.Image, FieldFile, ImageFieldFile)):
            fp.close()
        else:
            super().close(fp)

    @classmethod
    def optimize(
        cls,
        fp: _ImageFile,
        *,
        filename: str = None,
        upload_to: str = None,
        box: tuple[int, int, int, int] = None,
        max_width: int = app_settings.image_optimizer.max_width,
        max_height: int = app_settings.image_optimizer.max_height,
        to_webp: bool = app_settings.image_optimizer.to_webp,
        remove_origin: bool = app_settings.image_optimizer.remove_origin,
    ) -> tuple[_Image, str]:
        """Optimize the Image File

        Args:
          fp: File path or file object.
          filename: Rename the original file.
          upload_to: Upload dir.
          box: The crop rectangle, as a (left, upper, right, lower)-tuple to crop the image.
          max_width: Max width of the image to resize.
          max_height: Max height of the image to resize.
          to_webp: Force convert image to webp type.
          remove_origin: Force to delete original image after optimization.

        Returns:
          The Tuple: PIL Image, Image file path location. If the file is not in the correct format, a tuple with the value (None, None) can be returned.
        """

        image, path = cls.open(fp), None
        if not image:
            LOGGER.error("Image format not supported.")
            return image, path

        fm, ext = None, None
        if isinstance(image, PngImageFile):
            fm, ext = "PNG", ".png"
            image = image.convert("P", palette=Image.ADAPTIVE)
        elif isinstance(image, JpegImageFile):
            fm, ext = "JPEG", ".jpg"
        elif isinstance(image, WebPImageFile):
            fm, ext = "WEBP", ".webp"

        if app_settings.image_optimizer.to_webp:
            fm, ext = "WEBP", ".webp"

        if str(ext) in cls._supported_file_types:
            image = cls.crop(image, box=box)
            image = cls.resize(image, max_width, max_height)
            image.info = {}
            if not filename and not isinstance(filename, str):
                filename = str(
                    cls.get_identifier(fp.filename if isinstance(fp, _Image) else fp)
                )

            filename = filename + ext
            save_path, path = get_paths(filename, upload_to=upload_to)
            image.save(
                save_path,
                fm,
                optimize=True,
                quality=app_settings.image_optimizer.quality,
                compress_level=app_settings.image_optimizer.compress_level,
            )

            if remove_origin:
                LOGGER.info("Proceed to delete the original image file.")
                if isinstance(fp, (FieldFile, ImageFieldFile)):
                    if filename not in fp.name:
                        fp.delete(save=False)
                else:
                    origin_fp = (
                        getattr(fp, "name", None)
                        if isinstance(fp, (BytesIO, BufferedReader))
                        else fp
                    )
                    if (
                        origin_fp
                        and isinstance(origin_fp, str)
                        and path not in origin_fp
                    ):
                        safe_remove_file(origin_fp)
        else:
            LOGGER.error("Image format not supported.")
        return image, path

    @classmethod
    def crop(cls, image: _Image, box: tuple[int, int, int, int] = None) -> _Image:
        """Crop an image

        Args:
          image: PIL image object.
          box: The crop rectangle, as a (left, upper, right, lower)-tuple.

        Returns:
          Returns a rectangular region from this PIL image.
        """
        LOGGER.info("Proceed to crop image.")

        if image and box is not None:
            return image.crop(box)
        return image

    @classmethod
    def resize(
        cls,
        image: _Image,
        width: int = app_settings.image_optimizer.max_width,
        height: int = app_settings.image_optimizer.max_height,
    ) -> _Image:
        """Resize image to fit with Width and Height

        Args:
          image: PIL image object.
          width: Max width to resize.
          height: Max height to resize.

        Returns:
          PIL image after resizing
        """
        LOGGER.info("Proceed to reduce image size")

        w, h = image.size
        aspect_ratio = w / h

        if w > width or h > height:
            if aspect_ratio > 1:
                nw = width
                nh = int(width / aspect_ratio)
            else:
                nh = height
                nw = int(height * aspect_ratio)

            return image.resize((nw, nh), Image.LANCZOS)
        return image


MapOptimizer = {TypeChoices.IMAGE: ImageOptimizer}
