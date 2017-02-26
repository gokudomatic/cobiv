from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import AsyncImage
from kivy.uix.widget import Widget

from cobiv.modules.browser.item import Item
from cobiv.modules.component import Component
from cobiv.modules.view import View
from cobiv.libs.magnet import Magnet
from kivy.properties import ObjectProperty, NumericProperty, StringProperty

Builder.load_file('modules/browser/browser.kv')


class Thumb(BoxLayout):
    cell_size = NumericProperty(None)
    caption = StringProperty(None)
    source = StringProperty(None)

    def __init__(self, **kwargs):
        super(Thumb, self).__init__(**kwargs)


class Browser(View, FloatLayout):
    cell_size = NumericProperty(300)
    current_imageset = None

    grid = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Browser, self).__init__(**kwargs)

        self.set_action("load-set", self.load_set)

    def get_name(instance=None):
        return "browser"

    def build_config(self, config):
        Component.build_config(self, config)
        section = self.get_config_hotkeys_section()
        config.add_section(section)

    def ready(self):
        Component.ready(self)
        self.current_imageset = self.get_app().lookup("session", "Entity").get_currentset()

    def load_set(self):
        self.grid.clear_widgets()

        for filename in self.current_imageset.uris:
            image = Thumb(source=filename, cell_size=self.cell_size, caption="toto")
            draggable = Item(img=image, container=self,
                             cell_size=self.cell_size)
            self.grid.add_widget(draggable)
