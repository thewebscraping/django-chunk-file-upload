#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
django-chunk-file-upload
------------

Tests for `django-chunk-file-upload` models module.
"""

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.client import MULTIPART_CONTENT
from django.urls import reverse_lazy

from django_chunk_file_upload import permissions
from django_chunk_file_upload.app_settings import app_settings
from django_chunk_file_upload.models import FileManager
from django_chunk_file_upload.optimize import ImageOptimizer
from django_chunk_file_upload.utils import create_dir, remove_dir
from django_chunk_file_upload.views import ChunkedUploadView


class BaseTestCase(TestCase):
    """Base DjangoChunkFileUpload Test Case"""

    CHUNK_SIZE = 65536
    IMAGE_FILE = os.path.join(settings.BASE_DIR, "tests/media", "test.jpg")
    User = get_user_model()
    origin_image = None
    origin_image_checksum = None
    image = None
    image_path = None
    image_checksum = None
    username = password = "test"

    def setUp(self):
        create_dir(app_settings.upload_to)
        self.origin_image = ImageOptimizer.open(self.IMAGE_FILE)
        self.image, self.image_path = ImageOptimizer.optimize(
            self.IMAGE_FILE,
            filename=None,
            upload_to=app_settings.upload_to,
            max_width=600,
            max_height=600,
            remove_origin=False,
        )
        self.origin_image_checksum = ImageOptimizer.checksum(self.IMAGE_FILE)
        self.image_checksum = ImageOptimizer.checksum(
            os.path.join(settings.MEDIA_ROOT, self.image_path)
        )

    def test_image_optimize(self):
        self.assertNotEqual(
            self.origin_image.size,
            self.image.size,
            "Original image same size with optimized image.",
        )
        self.assertNotEqual(
            self.origin_image_checksum,
            self.image_checksum,
            "Original image checksum same with optimized image checksum.",
        )

    def tearDown(self):
        ImageOptimizer.close(self.origin_image)
        ImageOptimizer.close(self.image)
        remove_dir(app_settings.upload_to)


class TestDjangoChunkUploadView(BaseTestCase):
    file_stat = None
    chunk_from, chunk_to = None, None

    def setUp(self) -> None:
        super().setUp()
        self.file_stat = os.stat(self.IMAGE_FILE)
        self.chunk_from, self.chunk_to = 0, self.CHUNK_SIZE

    def _get_headers(self):
        return {
            "X-File-ID": None,
            "X-File-Name": "test.jpg",
            "X-File-Checksum": self.origin_image_checksum,
            "X-File-Chunk-From": self.chunk_from,
            "X-File-Chunk-Size": self.chunk_to,
            "X-File-Chunk-To": self.chunk_to,
            "X-File-EOF": bool(self.chunk_to > self.file_stat.st_size),
            "X-File-Size": self.file_stat.st_size,
            "X-File-MimeType": "image/jpeg",
        }

    def _get_response(self):
        with open(self.IMAGE_FILE, "rb") as f:
            chunk_from, chunk_to = 0, self.CHUNK_SIZE
            response = None
            while chunk := f.read(self.CHUNK_SIZE):
                response = self.client.post(
                    path=reverse_lazy("django_chunk_file_upload:uploads"),
                    data={"file": SimpleUploadedFile("test.jpg", chunk)},
                    content_type=MULTIPART_CONTENT,
                    headers=self._get_headers(),
                )
                chunk_from += self.CHUNK_SIZE
                chunk_to += self.CHUNK_SIZE

            return response

    def _create_user(self, is_superuser: bool = False, is_staff: bool = False):
        user, _ = self.User.objects.update_or_create(
            username=self.username,
            defaults=dict(
                email="test@example.com",
                password=self.password,
                is_active=True,
                is_staff=is_staff,
                is_superuser=is_superuser,
            ),
        )
        return user

    def _instance_validate(self):
        instance = FileManager.objects.filter(
            checksum=self.origin_image_checksum
        ).first()
        self.assertNotEqual(instance, None, "Not found file manager instance.")
        self.assertEqual(
            instance.checksum, self.origin_image_checksum, "Invalid MD5 checksum."
        )
        instance.delete()

    def test_upload_view_with_allow_any_permission(self):
        """Test ChunkedUploadView with AllowAny permission."""

        ChunkedUploadView.permission_classes = (permissions.AllowAny,)
        response = self._get_response()
        self.assertEqual(201, response.status_code, "Failed to upload files.")
        self._instance_validate()

    def test_upload_view_with_is_authenticated_permission(self):
        """Test ChunkedUploadView with IsAuthenticated permission."""

        ChunkedUploadView.permission_classes = (permissions.IsAuthenticated,)
        response = self._get_response()
        self.assertEqual(
            400, response.status_code, "Failed to test IsAuthenticated permission."
        )
        user = self._create_user()
        self.client.force_login(user)
        response = self._get_response()
        self.assertEqual(
            201, response.status_code, "Failed to test IsAuthenticated permission."
        )
        self._instance_validate()

    def test_upload_view_with_is_superuser_permission(self):
        """Test ChunkedUploadView with IsSuperUser permission."""

        ChunkedUploadView.permission_classes = (permissions.IsSuperUser,)
        response = self._get_response()
        self.assertEqual(
            400, response.status_code, "Failed to test IsSuperUser permission."
        )
        user = self._create_user(is_superuser=True)
        self.client.force_login(user)
        response = self._get_response()
        self.assertEqual(
            201, response.status_code, "Failed to test IsAuthenticated permission."
        )
        self._instance_validate()

    def test_upload_view_with_is_admin_user_permission(self):
        """Test ChunkedUploadView with IsAdminUser permission."""

        ChunkedUploadView.permission_classes = (permissions.IsAdminUser,)
        response = self._get_response()
        self.assertEqual(
            400, response.status_code, "Failed to test IsAdminUser permission."
        )
        user = self._create_user(is_staff=True)
        self.client.force_login(user)
        response = self._get_response()
        self.assertEqual(
            201, response.status_code, "Failed to test IsAuthenticated permission."
        )
        self._instance_validate()

    def test_upload_view_with_is_staff_permission(self):
        """Test uploading file with staff user."""

        ChunkedUploadView.permission_classes = (permissions.IsStaffUser,)
        response = self._get_response()
        self.assertEqual(
            400, response.status_code, "Failed to test IsStaffUser permission."
        )
        user = self._create_user(is_staff=True)
        self.client.force_login(user)
        response = self._get_response()
        self.assertEqual(
            201, response.status_code, "Failed to test IsAuthenticated permission."
        )
        self._instance_validate()


class TestImageOptimizer(BaseTestCase):
    def test_image_optimize(self):
        assert self.origin_image.size != self.image.size
        assert ImageOptimizer.checksum(self.IMAGE_FILE) != ImageOptimizer.checksum(
            os.path.join(settings.MEDIA_ROOT, self.image_path)
        )
