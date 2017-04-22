import os

from kivy.clock import Clock
from kivy.uix.image import AsyncImage


class ThumbnailImage(AsyncImage):
    file_exists = False

    def __init__(self, **kwargs):
        self.file_exists = os.path.exists(kwargs.get('source', ""))
        super(ThumbnailImage, self).__init__(**kwargs)

        if self.source != "" and self.source is not None and not self.file_exists:
            Clock.schedule_once(self.retry_load, 1)

    def retry_load(self, dt):
        self.file_exists = os.path.exists(self.source)
        if self.file_exists:
            self._load_source()
        else:
            Clock.schedule_once(self.retry_load, 1)