from __future__ import division

import os
from io import BytesIO

import sys
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.uix.image import AsyncImage
from enum import Enum
import PIL
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

Builder.load_file('modules/imageset/slide.kv')


class SlideMode(Enum):
    NORMAL = 0
    FIT_SCREEN = 1
    FIT_WIDTH = 2
    FIT_HEIGHT = 3


class Slide(AsyncImage):
    mode = ObjectProperty(None)
    load_mode = None

    is_loaded = False

    def __init__(self, load_mode=SlideMode.NORMAL, **kwargs):
        super(Slide, self).__init__(**kwargs)
        self.load_mode = load_mode
        self._coreimage.bind(on_load=self.on_image_loaded)
        self.bind(width=self.on_width)
        self.bind(height=self.on_height)
        self.bind(mode=self.on_mode)
        self.bind(texture_size=self.on_texture_size)

    def on_texture_size(self, instance, value):
        if self.is_loaded:
            self.mode = self.load_mode
            self.size = self.texture_size

    def on_image_loaded(self, *args):
        self.is_loaded = True

    def on_mode(self, obj, value):
        if value == SlideMode.FIT_HEIGHT:
            self.size_hint = (None, 1)
        elif value == SlideMode.FIT_WIDTH:
            self.size_hint = (1, None)
        elif value == SlideMode.FIT_SCREEN:
            self.size_hint = (1, 1)
        else:
            self.size_hint = (None, None)

        if value != SlideMode.NORMAL:
            self.size = self.texture_size

    def reset_zoom(self):
        self.size = self.texture_size

    def on_width(self, obj, value):
        if self.mode == SlideMode.FIT_WIDTH:
            self.height = self.width / self.image_ratio

    def on_height(self, obj, value):
        if self.mode == SlideMode.FIT_HEIGHT:
            self.width = self.height * self.image_ratio

    @property
    def zoom(self):
        return self.width / self.texture_size[0]

    @zoom.setter
    def zoom(self, value):
        if self.mode == SlideMode.NORMAL:
            self.width = self.texture_size[0] * value
            self.height = self.texture_size[1] * value


class ImageSet(EventDispatcher):
    uris = []
    marked = ListProperty([])

    current = None

    def __len__(self):
        return len(self.uris)

    def index_of(self, value):
        return self.uris.index(value)

    def image(self, idx, fit_mode):
        if 0 <= idx <= len(self.uris):
            return Slide(source=self.uris[idx], load_mode=fit_mode)
        else:
            return None

    def next(self, idx):
        if idx < len(self.uris) - 1:
            return idx + 1
        else:
            return 0

    def previous(self, idx):
        if idx == 0:
            return len(self.uris) - 1
        else:
            return idx - 1

    def remove(self, idx):
        filename = self.uris[idx]
        self.uris.remove(filename)
        return idx if idx < len(self.uris) else 0

    def mark_all(self, value=None):
        if value == None:
            value = len(self.marked) < len(self.uris)
        if value:
            self.marked = self.uris[:]
        else:
            self.marked = []

    def mark_invert(self):
        self.marked = list(set(self.uris) - set(self.marked))

    def mark(self, items, value=None):
        for item in items:
            is_marked = item in self.marked
            if value == None:
                value = not is_marked
            if value and not is_marked:
                self.marked.append(item)
            elif not value and is_marked:
                self.marked.remove(item)


def create_thumbnail_data(filename, size,destination):
    # print "creating thumbnail for "+filename
    img = Image.open(filename)
    try:
        img.load()
    except SyntaxError as e:
        path=os.path.dirname(sys.argv[0])
        destination='C:/Users/edwin/Apps/python/workspace/cobiv/cobiv\\resources\\icons\\image_corrupt.png'
        # destination=os.path.join(path,"resources","icons","image_corrupt.png")
        print(destination)
        return  destination
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

    image_byte_array = BytesIO()
    img.convert('RGB').save(destination, format='PNG',optimize=True)
    return destination
