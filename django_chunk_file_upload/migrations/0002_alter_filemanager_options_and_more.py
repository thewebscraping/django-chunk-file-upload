# Generated by Django 5.0.7 on 2024-08-19 20:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_chunk_file_upload", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="filemanager",
            options={
                "ordering": ("-created_at",),
                "verbose_name": "File Manager",
                "verbose_name_plural": "File Manager",
            },
        ),
        migrations.AddField(
            model_name="filemanager",
            name="type",
            field=models.CharField(
                choices=[
                    (None, "Unknown"),
                    ("ARCHIVE", "ARCHIVE"),
                    ("AUDIO", "AUDIO"),
                    ("BINARY", "BINARY"),
                    ("DOCUMENT", "DOCUMENT"),
                    ("FONT", "FONT"),
                    ("HYPERTEXT", "HYPERTEXT"),
                    ("IMAGE", "IMAGE"),
                    ("JSON", "JSON"),
                    ("MICROSOFT_EXCEL", "MICROSOFT_EXCEL"),
                    ("MICROSOFT_POWERPOINT", "MICROSOFT_POWERPOINT"),
                    ("MICROSOFT_WORD", "MICROSOFT_WORD"),
                    ("SOURCE_CODE", "SOURCE_CODE"),
                    ("SEPARATED", "SEPARATED"),
                    ("TEXT", "TEXT"),
                    ("VIDEO", "VIDEO"),
                    ("XML", "XML"),
                ],
                default="Unknown",
                max_length=255,
                verbose_name="Type",
            ),
        ),
        migrations.AddField(
            model_name="filemanager",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="files",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="filemanager",
            name="checksum",
            field=models.CharField(max_length=255),
        ),
        migrations.RemoveField(
            model_name="filemanager",
            name="name",
        ),
        migrations.AlterUniqueTogether(
            name="filemanager",
            unique_together={("user", "checksum")},
        ),
    ]
