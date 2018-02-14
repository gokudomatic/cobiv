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
    padding: 10
    orientation: 'vertical'
    BoxLayout:
        height: 64
        size_hint_y: None
        orientation: 'horizontal'
        Image:
            source: root.image_path
            width: self.height
            size_hint_x: None
        Label:
            font_size: self.height - dp(15)
            text: root.title
            text_size: self.size
            halign: 'left'
    Label:
        text: root.description
        halign: 'left'
        valign: 'top'
        text_size: self.size
        font_size: sp(20)
''')


class BookSlide(BoxLayout):
    title = StringProperty("")
    image_path = StringProperty(None)
    description = StringProperty("")

    def __init__(self, session=None, cursor=None, load_mode=None, **kwargs):
        super(BookSlide, self).__init__(**kwargs)

        self.file_id=cursor.file_id
        self.session = session
        self.title = cursor.filename
        self.image_path = os.path.join(os.path.dirname(sys.argv[0]), "resources", "icons", "book.png")

        self.load_content()

    def load_content(self):
        impl_name = 'sqlite_book_manager'
        book_mgr = self.session.lookup(impl_name, 'BookManager')
        details=book_mgr.get_list_detail(self.file_id)
        description=""
        for file_id,name,position in details:
            description+="{}. {}\r\n".format(position,name)
        self.description=description

    def reset_zoom(self):
        pass

    @property
    def zoom(self):
        return 1

    @zoom.setter
    def zoom(self, value):
        pass
