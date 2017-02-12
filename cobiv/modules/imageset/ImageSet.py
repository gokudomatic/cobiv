from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.image import AsyncImage
from enum import Enum

Builder.load_file('modules/imageset/slide.kv')

class SlideMode(Enum):
    NORMAL=0
    FIT_SCREEN=1
    FIT_WIDTH=2
    FIT_HEIGHT=3


class Slide(AsyncImage):

    mode=ObjectProperty(None)

    is_loaded=False

    def __init__(self, **kwargs):
        super(Slide, self).__init__(**kwargs)
        self._coreimage.bind(on_load=self.on_image_loaded)
        self.bind(width=self.on_width)
        self.bind(height=self.on_height)
        self.bind(mode=self.on_mode)
        self.bind(texture_size=self.on_texture_size)

    def on_texture_size(self, instance, value):
        if self.is_loaded:
            self.mode=SlideMode.FIT_HEIGHT


    def on_image_loaded(self,*args):
        self.is_loaded=True

    def on_mode(self,obj,value):
        print "mode="+str(value)
        if value==SlideMode.FIT_HEIGHT:
            self.size_hint=(None,1)
        elif value==SlideMode.FIT_WIDTH:
            self.size_hint=(1,None)
        elif value==SlideMode.FIT_SCREEN:
            self.size_hint=(1,1)
        else:
            self.size_hint=(None,None)
            self.size=self.texture_size
        self.size=self.texture_size
        print "size_hint: "+str(self.size_hint)
        print "texture_size"+str(self.texture_size)


    def on_width(self,obj,value):
        if self.mode==SlideMode.FIT_WIDTH:
            self.height = self.width / self.image_ratio

    def on_height(self,obj,value):
        if self.mode==SlideMode.FIT_HEIGHT:
            self.width = self.height * self.image_ratio


    @property
    def zoom(self):
        return self.width/self.texture_size[0]

class ImageSet:
    uris = []

    def images(self):
        for uri in self.uris:
            yield Slide(source=uri)


current_imageset = ImageSet()
