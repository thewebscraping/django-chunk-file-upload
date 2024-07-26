# Django Chunk File Upload

Django Chunk File Upload is an alternative utility that helps you easily edit Django's chunked, drag and drop file uploads.

<img src="https://i.ibb.co/9y2SgmS/f-P5-Or-Gkxk0-Ynj00ct-G.webp" alt="f-P5-Or-Gkxk0-Ynj00ct-G" border="0">

Features
----------
- Multiple file uploads.
- Drag and Drop UI.
- MD5 checksum file.
- Chunked uploads: optimizing large file transfers.
- Prevent uploading existing files with MD5 checksum.
- Easy to use any models.


Quickstart
----------

Install Django Chunk File Upload:
```shell
pip install git+https://github.com/thewebscraping/django-chunk-file-upload.git
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
    "chunk_size": 1024 * 1024 * 2,  # # custom chunk size upload (default: 2MB).
    "upload_to": "custom_folder/%Y/%m/%d",  # custom upload folder.
    "is_metadata_storage": True,  # save file metadata
    "js": (
        "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/spark-md5/3.0.2/spark-md5.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.js",
    ),  # use cdn.
    "css": (
        "custom.css"
     )  # custom css path.
}

```

Custom Your Models
----------

models.py

```python
from django.db import models
from django_chunk_file_upload.models import FileManager


class Tag(models.Model):
    name = models.CharField(max_length=255)


class YourModel(FileManager):
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

```python
from django_chunk_file_upload.views import ChunkedUploadView
from .forms import YourForm


class CustomChunkedUploadView(ChunkedUploadView):
    form_class = YourForm
    # chunk_size = 1024 * 1024 * 2  # custom chunk size upload (default: 2MB).
    # upload_to = "custom_folder/%Y/%m/%d"  # custom upload folder.
    # template_name = "custom_template.html"  # custom template
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

This package is under development, only supports create view. There are also no features related to image optimization. Use at your own risk.
