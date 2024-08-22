from PIL import Image, UnidentifiedImageError
from PIL.JpegImagePlugin import JpegImageFile
from PIL.PngImagePlugin import PngImageFile
from PIL.WebPImagePlugin import WebPImageFile

from .app_settings import app_settings
from .constants import TypeChoices
from .utils import get_file_path


class BaseOptimizer:
    """Base Optimizer"""

    def __init__(self, instance, file, *args, **kwargs):
        self._instance = instance
        self._file = file

    @property
    def instance(self):
        return self._instance

    @property
    def file(self):
        return self._file

    def optimize(self):
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

    def open(self) -> Image.Image | None:
        try:
            image = Image.open(self.file.file)
            return image
        except UnidentifiedImageError:
            pass

    def close(self, image: Image.Image) -> None:
        if isinstance(image, Image.Image):
            image.close()

    def optimize(self) -> None:
        resized_img = self.open()
        if not resized_img:
            return

        fm, ext = None, None
        if isinstance(resized_img, PngImageFile):
            fm, ext = "PNG", ".png"
            resized_img = resized_img.convert("P", palette=Image.ADAPTIVE)
        elif isinstance(resized_img, JpegImageFile):
            fm, ext = "JPEG", ".jpg"
        elif isinstance(resized_img, WebPImageFile):
            fm, ext = "WEBP", ".webp"

        if app_settings.image_optimizer.to_webp:
            fm, ext = "WEBP", ".webp"

        if str(ext) in self._supported_file_types:
            resized_img = self.resize(resized_img)
            orig_save_path = self.file.save_path
            filename = self.file.repl_filename + ext
            self.file.path = get_file_path(filename, self.file._upload_to)
            resized_img.save(
                self.file.save_path,
                fm,
                optimize=True,
                quality=app_settings.image_optimizer.quality,
                compress_level=app_settings.image_optimizer.compress_level,
            )
            if orig_save_path != self.file.save_path:
                self.instance.file.delete()
                self.file.extension = ext

        self.close(resized_img)

    def resize(self, image: Image.Image) -> Image.Image:
        """Resize image to fit with max width and max height"""

        w, h = image.size
        aspect_ratio = w / h

        if (
            w > app_settings.image_optimizer.max_width
            or h > app_settings.image_optimizer.max_height
        ):
            if aspect_ratio > 1:
                nw = app_settings.image_optimizer.max_width
                nh = int(app_settings.image_optimizer.max_width / aspect_ratio)
            else:
                nh = app_settings.image_optimizer.max_height
                nw = int(app_settings.image_optimizer.max_height * aspect_ratio)

            return image.resize((nw, nh), Image.LANCZOS)
        return image


MapOptimizer = {TypeChoices.IMAGE: ImageOptimizer}
