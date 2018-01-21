import os
from kivy.clock import Clock
from kivy.uix.image import AsyncImage


class BookBrowserThumbnail(AsyncImage):
    file_exists = False

    def __init__(self, **kwargs):
        source = kwargs.pop('source', "")
        self.file_exists = os.path.exists(source)
        super().__init__(source=source, **kwargs)

        if self.source != "" and self.source is not None and not self.file_exists:
            Clock.schedule_once(self.retry_load, 1)

    def retry_load(self, dt):
        self.file_exists = os.path.exists(self.source)
        if self.file_exists:
            self._load_source()
        elif self.parent is not None:
            Clock.schedule_once(self.retry_load, 1)
