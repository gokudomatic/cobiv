import os
import threading

import time
from collections import deque
from functools import partial

from kivy.app import App
from kivy.cache import Cache
from kivy.clock import Clock
from kivy.uix.image import AsyncImage

from cobiv.modules.browser.item import Thumb
from cobiv.modules.imageset.ImageSet import create_thumbnail_data


class ThumbLoader():
    container = None

    thread = None
    thread_alive = True
    cell_size = 120

    to_cache = deque()

    def __init__(self):
        Cache.register('browser_items', limit=self.get_config_value('browser.cache.thumbnails.size', 500))

    def stop(self):
        self.thread_alive = False

    def restart(self):
        if self.thread is not None and self.thread.is_alive:
            self.thread_alive = False
            self.thread.join()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        thumb_path = self.get_config_value('thumbnails.path')
        self.thread_alive = True

        try:
            while self.thread_alive:
                try:
                    file_id, filename = self.to_cache.popleft()

                    thumb_filename = os.path.join(thumb_path, str(file_id) + '.png')
                    if not os.path.exists(thumb_filename):
                        create_thumbnail_data(filename, self.cell_size, thumb_filename)
                        time.sleep(0.5)

                    # if Cache.get('browser_items', file_id) is None:
                    #     Clock.schedule_once(partial(self._create_item, file_id, thumb_filename,filename), 0.1)
                    #     time.sleep(0.1)
                except IndexError:
                    time.sleep(0.5)

        except KeyboardInterrupt:
            pass

    # def _create_item(self, file_id, filename, original_filename, *largs):
    #     name = self.get_filename_caption(original_filename)
    #     item = AsyncImage(source=filename, mipmap=True, allow_stretch=True, keep_ration=True)
    #     thumb = Thumb(image=item, cell_size=self.cell_size, caption=name, selected=False)
    #     Cache.append('browser_items', file_id, thumb)

    def append(self, *items):
        for item in items:
            self.to_cache.append(item)

    def get_filename_caption(self, filename):
        name = os.path.basename(filename)
        if len(name) > 12:
            name = name[:5] + "..." + name[-7:]
        return name

    def get_image(self, file_id, filename, caption, force_refresh=False):
        thumb = None
        # thumb = Cache.get('browser_items', file_id)
        if thumb is None or force_refresh:
            name = self.get_filename_caption(caption)
            img = AsyncImage(source=filename, mipmap=True, allow_stretch=True, keep_ration=True)
            thumb = Thumb(image=img, cell_size=self.cell_size, caption=name, selected=False)
            # Cache.append('browser_items', file_id, thumb)
        return thumb

    # def invalidate_image(self, file_id):
    #     Cache.remove('browser_items', file_id)

    def get_config_value(self, key, default=None):
        return App.get_running_app().get_config_value(key, default=default)
