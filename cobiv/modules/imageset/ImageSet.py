from __future__ import division

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.image import AsyncImage
from enum import Enum


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
