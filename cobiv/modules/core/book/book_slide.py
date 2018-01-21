from __future__ import division

import os, io
from kivy.core.image import Image as CoreImage
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from enum import Enum

Builder.load_string('''
#:kivy 1.9.1
#:import win kivy.core.window

<BookSlide>:
    orientation: 'vertical'
    BoxLayout:
        orientation: 'horizontal'
        Image:
            id: thumb
        Label:
            id: title
            font_size: self.height - dp(15)
    Label:
        id: description
''')


class BookSlide(BoxLayout):

    def __init__(self, filename=None, ext=None, repo_key=None, session=None, **kwargs):
        super(BookSlide, self).__init__(**kwargs)

        file_fs = session.get_filesystem(repo_key)
        memory_data = file_fs.getbytes(filename)

        im = CoreImage(io.BytesIO(memory_data), ext=ext)

    def reset_zoom(self):
        pass

    @property
    def zoom(self):
        return 1

    @zoom.setter
    def zoom(self, value):
        pass