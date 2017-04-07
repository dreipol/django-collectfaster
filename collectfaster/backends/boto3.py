# -*- coding: utf-8 -*-
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class S3Boto3StaticStorage(S3Boto3Storage):
    location = getattr(settings, 'STATICFILES_LOCATION', 'static')


class S3Boto3MediaStorage(S3Boto3Storage):
    location = getattr(settings, 'MEDIAFILES_LOCATION', 'media')
