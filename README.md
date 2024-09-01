# Django Chunk File Upload

Django Chunk File Upload is an alternative utility that helps you easily edit Django's chunked, drag and drop file uploads.

<img src="https://i.ibb.co/9y2SgmS/f-P5-Or-Gkxk0-Ynj00ct-G.webp" alt="f-P5-Or-Gkxk0-Ynj00ct-G">

Features
----------
- Multiple file uploads.
- Drag and Drop UI.
- MD5 checksum file: check, validate, handle duplicate files.
- Chunked uploads: optimizing large file transfers.
- Prevent uploading existing files with MD5 checksum.
- Easy to use any models.
- Image optimizer, resizer, auto convert to webp (supported webp, png, jpg, jpeg).
- Permissions.


Quickstart
----------

Install Django Chunk File Upload:
```shell
pip install git+https://github.com/thewebscraping/django-chunk-file-upload.git
```

Pypi:
```shell
pip install django-chunk-file-upload
```

Add it to your `settings.py`:

```python
INSTALLED_APPS = [
    'django_chunk_file_upload',
]
```

Add it to your `urls.py`:


```python
from django.urls import path, include

urlpatterns = [
    path("file-manager/", include("django_chunk_file_upload.urls")),
]
```

Run Demo

Demo URL: http://127.0.0.1:8000/file-manager/uploads/
```shell
cd examples
python manage.py migrate
python manage.py runserver
```

Change default config: `settings.py`

```python
DJANGO_CHUNK_FILE_UPLOAD = {
    "chunk_size": 1024 * 1024 * 2,  # # Custom chunk size upload (default: 2MB).
    "upload_to": "uploads/%Y/%m/%d",  # Custom upload folder.
    "is_metadata_storage": True,  # Save file metadata,
    "remove_file_on_update": True,
    "optimize": True,
    "image_optimizer": {
        "quality": 82,
        "compress_level": 9,
        "max_width": 1024,
        "max_height": 720,
        "to_webp": True,  # Force convert image to webp type.
        "remove_origin": True,  # Force to delete original image after optimization.
    },
    "permission_classes": ("django_chunk_file_upload.permissions.AllowAny",),  # default: IsAuthenticated
    # "js": (
    #     "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js",
    #     "https://cdnjs.cloudflare.com/ajax/libs/spark-md5/3.0.2/spark-md5.min.js",
    #     "https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.js",
    # ),  # custom js, use cdn.
    # "css": ("custom.css",),  # custom your css path.
}

```

Custom Your Models
----------

models.py

```python
from django.db import models
from django_chunk_file_upload.models import FileManagerMixin


class Tag(models.Model):
    name = models.CharField(max_length=255)


class YourModel(FileManagerMixin):
    tags = models.ManyToManyField(Tag)
    custom_field = models.CharField(max_length=255)

```

forms.py

```python
from django_chunk_file_upload.forms import ChunkedUploadFileForm
from .models import YourModel


class YourForm(ChunkedUploadFileForm):
    class Meta:
        model = YourModel
        fields = "__all__"
```

views.py

Accepted methods: GET, POST, DELETE (UPDATE, PUT does not work with FormData).
```python
from django_chunk_file_upload.views import ChunkedUploadView
from django_chunk_file_upload.typed import File
from django_chunk_file_upload.permissions import IsAuthenticated
from .forms import YourForm


class CustomChunkedUploadView(ChunkedUploadView):
    form_class = YourForm
    permission_classes = (IsAuthenticated,)

    # file_class = File  # File handle class
    # file_status = app_settings.status  # default: PENDING (Used when using background task, you can change it to COMPLETED.)
    # optimize = True  # default: True
    # remove_file_on_update = True  # Update image on admin page.
    # chunk_size = 1024 * 1024 * 2  # Custom chunk size upload (default: 2MB).
    # upload_to = "custom_folder/%Y/%m/%d"  # Custom upload folder.
    # template_name = "custom_template.html"  # Custom template

    # # Run background task like celery when upload is complete
    # def background_task(self, instance):
    #     pass
```

custom_template.html
```html
<form action="."
      method="post"
      id="chunk-upload-form">
    {{ form.media }}
    {{ form }}
</form>
```

urls.py

```pyhon
from django.urls import path

from .views import CustomChunkedUploadView

urlpatterns = [
    path("uploads/", CustomChunkedUploadView.as_view(), name="custom-uploads"),
]
```

### Permissions
```python
from django_chunk_file_upload.permissions import AllowAny, IsAuthenticated, IsAdminUser, IsSuperUser
```

### File Handlers
```python
from django_chunk_file_upload.typed import (
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
```

### Image Optimizer
Use image Optimizer feature for other modules

```python
from django_chunk_file_upload.optimize import ImageOptimizer
from django_chunk_file_upload.app_settings import app_settings

# Image optimize method: resize, crop, delete, convert and optimize
# This method calls two other methods:
#   ImageOptimizer.resize: resize image
#   ImageOptimizer.crop: example get parameters from Cropperjs (https://github.com/fengyuanchen/cropperjs).
image, path = ImageOptimizer.optimize(
    fp='path/image.png',
    filename=None,  # Rename the original file.
    upload_to=None,  # Upload dir.
    box=None,  # The crop rectangle, as a (left, upper, right, lower)-tuple to crop the image.
    max_width =app_settings.image_optimizer.max_width,  # Max width of the image to resize.
    max_height=app_settings.image_optimizer.max_height,  # Max height of the image to resize.
    to_webp=True,  # Force convert image to webp type.
    remove_origin =app_settings.image_optimizer.remove_origin,  # Force to delete original image after optimization.
)
```

### UnitTests

```shell
python runtests.py
```

Note: This package is under development, only supports create view. There are also no features related to image optimization. Use at your own risk.
