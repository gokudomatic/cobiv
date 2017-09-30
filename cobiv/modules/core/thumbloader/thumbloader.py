import logging
import io,os
import sys
import threading
import time
from collections import deque
from os.path import expanduser

import PIL
from PIL import Image, ImageFile

from cobiv.modules.core.entity import Entity

ImageFile.LOAD_TRUNCATED_IMAGES = True


class ThumbLoader(Entity):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(ThumbLoader, self).__init__()
        self.to_cache = deque()
        self.container = None
        self.thread = None
        self.thread_alive = True
        self.cell_size = 120
        self.thumb_path = None
        self.queue_empty = True
        self.session = self.lookup("session", "Entity")

    def ready(self):
        super(ThumbLoader, self).ready()
        self.cell_size = int(self.get_config_value('image_size', 120))
        self.thumb_path = self.get_config_value('path')
        self.get_app().register_event_observer('on_file_content_change', self.delete_thumbnail)

    def build_yaml_config(self, config):
        config[self.get_name()] = {
            'image_size': 120,
            'path': os.path.join(expanduser('~'), '.cobiv', 'thumbnails')
        }
        return config

    def get_name(self=None):
        return "thumbloader"

    def stop(self):
        self.thread_alive = False
        self.thread.join()

    def restart(self):
        if self.thread is not None and self.thread.is_alive:
            self.thread_alive = False
            self.thread.join()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def get_fullpath_from_file_id(self, file_id):
        return os.path.join(self.thumb_path, str(file_id) + '.png')

    def run(self):
        self.thread_alive = True
        try:
            while self.thread_alive:
                if not self.queue_empty:
                    try:
                        file_id, filename, repo_key = self.to_cache.popleft()

                        thumb_filename = self.get_fullpath_from_file_id(file_id)
                        if not os.path.exists(thumb_filename):
                            self.create_thumbnail_data(repo_key, filename, self.cell_size, thumb_filename)
                    except IndexError:
                        self.queue_empty = True
                    time.sleep(0.5)

        except KeyboardInterrupt:
            pass

    def append(self, *items):
        for item in items:
            self.to_cache.append(item)
            self.queue_empty = False

    def clear_cache(self):
        self.to_cache.clear()

    def get_filename_caption(self, filename):
        name = os.path.basename(filename)
        if len(name) > 12:
            name = name[:5] + "..." + name[-7:]
        return name

    def delete_thumbnail(self, *items):
        for file_id in items:
            try:
                os.remove(self.get_fullpath_from_file_id(file_id))
            except WindowsError:
                pass

    def create_thumbnail_data(self, repo_key, filename, size, destination):
        self.logger.debug("creating thumbnail for " + filename)

        file_fs=self.session.get_filesystem(repo_key)
        data=file_fs.getbytes(filename)
        img = Image.open(io.BytesIO(data))
        try:
            img.load()
        except SyntaxError as e:
            path = os.path.dirname(sys.argv[0])
            destination = os.path.join(path, "resources", "icons", "image_corrupt.png")
            self.logger.error("Failed to read default thumbnail at : " + destination)
            self.logger.error(e, exc_info=True)
            return destination
        except:
            pass

        if img.size[1] > img.size[0]:
            baseheight = size
            hpercent = (baseheight / float(img.size[1]))
            wsize = int((float(img.size[0]) * float(hpercent)))
            hsize = size
        else:
            basewidth = size
            wpercent = (basewidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            wsize = size
        img = img.resize((wsize, hsize), PIL.Image.ANTIALIAS)

        img.convert('RGB').save(destination, format='PNG', optimize=True)
        return destination
