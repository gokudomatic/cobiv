from __future__ import division

import os, io
from kivy.core.image import Image as CoreImage
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.image import Image
from enum import Enum

Builder.load_file(os.path.abspath(os.path.join(os.path.dirname(__file__), 'slide.kv')))


class SlideMode(Enum):
    NORMAL = 0
    FIT_SCREEN = 1
    FIT_WIDTH = 2
    FIT_HEIGHT = 3


class Slide(Image):
    mode = ObjectProperty(None)
    load_mode = None

    is_loaded = True

    def __init__(self, session=None, load_mode=SlideMode.NORMAL, cursor=None, **kwargs):
        super(Slide, self).__init__(**kwargs)
        self.load_mode = load_mode
        self.bind(width=self.on_width)
        self.bind(height=self.on_height)
        self.bind(mode=self.on_mode)
        self.bind(texture_size=self.on_texture_size)

        file_fs = session.get_filesystem(cursor.repo_key)
        memory_data = file_fs.getbytes(cursor.filename)

        im = CoreImage(io.BytesIO(memory_data), ext=cursor.get_tag(0, 'ext', 0))

        self.texture = im.texture

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
            zoom_factor = min(self.width / self.texture_size[0], self.height / self.texture_size[1])
            self.size_hint = (None, None)
            self.zoom = zoom_factor

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
