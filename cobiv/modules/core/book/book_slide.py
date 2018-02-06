from __future__ import division

import os, io

import sys
from kivy.core.image import Image as CoreImage
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
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
            source: root.image_path
        Label:
            font_size: self.height - dp(15)
            text: root.title
    Label:
        text: root.description
''')


class BookSlide(BoxLayout):
    title = StringProperty("")
    image_path = StringProperty(None)
    description = StringProperty("")

    def __init__(self, session=None, cursor=None, load_mode=None, **kwargs):
        super(BookSlide, self).__init__(**kwargs)

        self.session = session
        self.title=cursor.filename
        self.image_path=os.path.join(os.path.dirname(sys.argv[0]), "resources", "icons", "book.png")

        self.load_content()

    def load_content(self):
        book_mgr=self.session.lookup()

    def reset_zoom(self):
        pass

    @property
    def zoom(self):
        return 1

    @zoom.setter
    def zoom(self, value):
        pass
