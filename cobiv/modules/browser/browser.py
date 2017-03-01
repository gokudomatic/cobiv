from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from cobiv.modules.browser.item import Item
from cobiv.modules.component import Component
from cobiv.modules.view import View
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
import os

Builder.load_file('modules/browser/browser.kv')


class Thumb(BoxLayout):
    cell_size = NumericProperty(None)
    caption = StringProperty(None)
    source = StringProperty(None)
    selected = BooleanProperty(None)
    marked = BooleanProperty(None)

    def __init__(self, **kwargs):
        super(Thumb, self).__init__(**kwargs)


class Browser(View, FloatLayout):
    cell_size = NumericProperty(120)
    current_imageset = None
    selected_idx = NumericProperty(None)
    old_selected_image = None
    grid = ObjectProperty(None)

    session = None

    def __init__(self, **kwargs):
        super(Browser, self).__init__(**kwargs)

        self.bind(selected_idx=self.current_idx_change)

        self.set_action("load-set", self.load_set)
        self.set_action("next", self.select_next)
        self.set_action("down", self.select_down)
        self.set_action("previous", self.select_previous)
        self.set_action("up", self.select_up)
        self.set_action("mark", self.mark_current)

    def get_name(self):
        return "browser"

    def build_config(self, config):
        Component.build_config(self, config)
        section = self.get_config_hotkeys_section()
        config.add_section(section)
        config.set(section, "next", "275")
        config.set(section, "previous", "276")
        config.set(section, "down", "274")  # down arrow
        config.set(section, "up", "273")  # up arrow
        config.set(section, "mark", "32")  # space
        config.set(section, "switch-view viewer", "13")  # space

    def ready(self):
        Component.ready(self)
        self.session = self.get_app().lookup("session", "Entity")
        self.current_imageset = self.session.get_currentset()

    def on_switch(self):
        self.load_set()
        if self.old_selected_image!=None:
            Clock.schedule_once(self.scroll_to_image)

    def scroll_to_image(self,dt):
        self.ids.scroll_view.scroll_to(self.old_selected_image)

    def load_set(self):
        self.grid.clear_widgets()

        if self.current_imageset==None:
            return

        for filename in self.current_imageset.uris:
            name=os.path.basename(filename)
            if len(name)>12:
                name=name[:5]+"..."+name[-7:]
            image = Thumb(source=filename, cell_size=self.cell_size, caption=name)
            draggable = Item(img=image, container=self,
                             cell_size=self.cell_size)
            self.grid.add_widget(draggable)

        idx=self.session.current_imageset_index
        self.selected_idx = -1
        self.selected_idx = idx

    def select_next(self):
        self.selected_idx += 1

    def select_down(self):
        self.select_row(1)

    def select_up(self):
        self.select_row(-1)

    def select_row(self, diff):
        linenr = self.selected_idx / self.grid.cols
        colnr = self.selected_idx % self.grid.cols
        self.selected_idx = colnr + (linenr + diff) * self.grid.cols

    def select_previous(self):
        self.selected_idx -= 1

    def current_idx_change(self, instance, value):
        if len(self.current_imageset)==0:
            return
        elif value < 0:
            self.selected_idx = 0
        elif value >= len(self.current_imageset):
            self.selected_idx = len(self.current_imageset) - 1
        elif value == None:
            if self.old_selected_image != None:
                self.old_selected_image.img.selected = False
            self.old_selected_image = None
        else:
            if self.old_selected_image != None:
                self.old_selected_image.img.selected = False
            img = self.grid.children[len(self.current_imageset) - 1 - value]
            img.img.selected = True
            self.old_selected_image = img
            self.ids.scroll_view.scroll_to(img)

            # update selected image
            self.session.current_imageset_index = value

    def on_image_touch_up(self, img):
        # select item
        self.selected_idx = self.index_of_image(img)

    def index_of_image(self, img):
        return len(self.current_imageset) - 1 - self.grid.children.index(img)

    def mark_current(self,value=None):
        thumb=self.old_selected_image
        if value==None:
            thumb.img.marked=not thumb.img.marked
        else:
            thumb.img.marked=value==True