# -*- coding: utf-8 -*-
from django.conf import settings
from storages.backends.s3boto import S3BotoStorage


class S3StaticStorage(S3BotoStorage):
    location = getattr(settings, 'STATICFILES_LOCATION', 'static')


class S3MediaStorage(S3BotoStorage):
    location = getattr(settings, 'MEDIAFILES_LOCATION', 'media')
