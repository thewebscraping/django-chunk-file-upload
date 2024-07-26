from __future__ import annotations

from django.conf import settings


class LazySettings:
    def __init__(self):
        self.css = ("css/upload.chunk.css", "css/toastr.min.css")
        self.js = (
            "js/jquery-3.7.1.min.js",
            "js/spark-md5.min.js",
            "js/toastr.min.js",
            "js/upload.chunk.js",
        )
        self.upload_to = "%Y/%m/%d"
        self.chunk_size = 1024 * 1024 * 2  # 2MB
        self.is_metadata_storage = True

    @classmethod
    def from_kwargs(cls, **kwargs) -> "LazySettings":
        ret = cls()
        for k, v in kwargs.items():
            if hasattr(ret, k) and v is not None:
                if k == "js":
                    v = list(set(list(ret.js) + ["js/upload.chunk.js"]))
                setattr(ret, k, v)
        return ret


app_settings = LazySettings.from_kwargs(
    **getattr(settings, "DJANGO_CHUNK_FILE_UPLOAD", {})
)
