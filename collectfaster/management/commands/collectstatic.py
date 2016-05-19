# -*- coding: utf-8 -*-
import time

from django.contrib.staticfiles.management.commands import collectstatic
from gevent import joinall, monkey, spawn
from gevent.queue import Queue


class Command(collectstatic.Command):
    """
    This command extends Django's `collectstatic` with a `--faster` argument for parallel file copying using gevent.
    The speed improvement is especially helpful for remote storage backends like S3.
    """
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.counter = 0
        self.gevent_task_queue = Queue()

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--faster', action='store_true', default=False, help='Collect static files simultaneously')
        parser.add_argument('--workers', action='store', default=20, help='Amount of simultaneous workers (default=20)')

    def set_options(self, **options):
        self.faster = options.pop('faster')
        self.queue_worker_amount = int(options.pop('workers'))
        super(Command, self).set_options(**options)

    def handle(self, **options):
        start_time = time.time()
        super(Command, self).handle(**options)
        self.log('%s static files copied asynchronously in %is.' % (self.counter, time.time() - start_time), level=1)

    def copy_file(self, path, prefixed_path, source_storage):
        self.file_handler('copy', path, prefixed_path, source_storage)

    def link_file(self, path, prefixed_path, source_storage):
        self.file_handler('link', path, prefixed_path, source_storage)

    def file_handler(self, handler_type, path, prefixed_path, source_storage):
        """
        Create a dict with all kwargs of the `copy_file` or `link_file` method of the super class and add it to
        the queue for later processing.
        """
        if self.faster:
            self.gevent_task_queue.put({
                'handler_type': handler_type,
                'path': path,
                'prefixed_path': prefixed_path,
                'source_storage': source_storage
            })
            self.counter += 1
        else:
            if handler_type == 'link':
                super(Command, self).link_file(path, prefixed_path, source_storage)
            else:
                super(Command, self).copy_file(path, prefixed_path, source_storage)

    def delete_file(self, path, prefixed_path, source_storage):
        """
        We don't need all the file_exists stuff because we have to override all files anyways.
        """
        if self.faster:
            return True
        else:
            return super(Command, self).delete_file(path, prefixed_path, source_storage)

    def collect(self):
        """
        Create some concurrent workers that process the tasks simultaneously.
        """
        result = super(Command, self).collect()
        if self.faster:
            monkey.patch_all(thread=False)
            joinall([spawn(self.gevent_worker) for x in range(self.queue_worker_amount)])
        return result

    def gevent_worker(self):
        """
        Process one task after another by calling the handler (`copy_file` or `copy_link`) method of the super class.
        """
        while not self.gevent_task_queue.empty():
            task_kwargs = self.gevent_task_queue.get()
            handler_type = task_kwargs.pop('handler_type')

            if handler_type == 'link':
                super(Command, self).link_file(**task_kwargs)
            else:
                super(Command, self).copy_file(**task_kwargs)
