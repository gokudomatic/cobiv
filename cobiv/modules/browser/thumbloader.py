import os
import threading

import time
from collections import deque

import sys
from kivy.app import App
from kivy.cache import Cache

from cobiv.modules.browser.ThumbnailImage import ThumbnailImage
from cobiv.modules.browser.item import Thumb

import PIL
from PIL import Image, ImageFile


ImageFile.LOAD_TRUNCATED_IMAGES = True

def create_thumbnail_data(filename, size, destination):
    # print "creating thumbnail for "+filename
    img = Image.open(filename)
    try:
        img.load()
    except SyntaxError as e:
        path = os.path.dirname(sys.argv[0])
        destination = 'C:/Users/edwin/Apps/python/workspace/cobiv/cobiv\\resources\\icons\\image_corrupt.png'
        # destination=os.path.join(path,"resources","icons","image_corrupt.png")
        print(destination)
        return destination
        print("error, not possible!")
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

    # image_byte_array = BytesIO()
    img.convert('RGB').save(destination, format='PNG', optimize=True)
    return destination


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

                except IndexError:
                    time.sleep(0.5)

        except KeyboardInterrupt:
            pass

    def append(self, *items):
        for item in items:
            self.to_cache.append(item)

    def clear_cache(self):
        self.to_cache.clear()

    def get_filename_caption(self, filename):
        name = os.path.basename(filename)
        if len(name) > 12:
            name = name[:5] + "..." + name[-7:]
        return name

    def get_image(self, file_id, filename, image_full_path, force_refresh=False):
        if not os.path.exists(filename):
            self.append((file_id, image_full_path))
        name = self.get_filename_caption(image_full_path)
        img = ThumbnailImage(source=filename, mipmap=True, allow_stretch=True, keep_ration=True)
        thumb = Thumb(image=img, cell_size=self.cell_size, caption=name, selected=False)
        return thumb

    def get_config_value(self, key, default=None):
        return App.get_running_app().get_config_value(key, default=default)
