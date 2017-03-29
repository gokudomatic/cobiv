import threading
from collections import deque

from kivy.app import App
from kivy.atlas import CoreImage
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import AsyncImage, Image
from kivy.core.image import Image as CoreImage
from kivy.uix.scrollview import ScrollView

from cobiv.modules.browser.item import Item
from cobiv.modules.component import Component
from cobiv.modules.view import View
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock, mainthread
import os

Builder.load_file('modules/browser/browser.kv')


class VerticalLoadEffect(DampedScrollEffect):
    def __init__(self, **kwargs):
        super(VerticalLoadEffect, self).__init__(**kwargs)
        self.trigger_load_next = Clock.create_trigger(self.load_next, 0.5)
        self.trigger_load_previous = Clock.create_trigger(self.load_prev, 0.5)

    def on_overscroll(self, *args):
        super(VerticalLoadEffect, self).on_overscroll(*args)
        if self.overscroll < -50:
            self.trigger_load_previous()
        elif self.overscroll > 50:
            self.trigger_load_next()

    def load_prev(self, dt):
        App.get_running_app().root.get_view().load_more_previous()

    def load_next(self, dt):
        App.get_running_app().root.get_view().load_more_next()


class ThumbScrollView(ScrollView):
    def __init__(self, **kwargs):
        super(ThumbScrollView, self).__init__(effect_cls=VerticalLoadEffect, **kwargs)


class Thumb(BoxLayout):
    cell_size = NumericProperty(None)
    caption = StringProperty(None)

    source = StringProperty(None)
    selected = BooleanProperty(None)
    marked = BooleanProperty(None)
    image = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Thumb, self).__init__(**kwargs)
        if kwargs.has_key('data'):
            data = kwargs['data']
            core = CoreImage(data, ext="png")
            self.image = AsyncImage(texture=core.texture, mipmap=True, allow_stretch=True, keep_ration=True)
        else:
            self.image = AsyncImage(source=kwargs['source'], mipmap=True, allow_stretch=True, keep_ration=True)
        self.add_widget(self.image, 1)


class Browser(View, FloatLayout):
    cell_size = NumericProperty(120)
    cursor = None
    page_cursor = None
    selected_image = None
    grid = ObjectProperty(None)
    max_rows = NumericProperty(None)
    max_scroll_ratio = NumericProperty(20)
    page_rows = NumericProperty(None)
    global_scroll_pos = NumericProperty(0)
    session = None

    image_queue = deque()
    append_queue = True

    pending_actions = deque()

    widget_to_scroll=None

    def __init__(self, **kwargs):
        super(Browser, self).__init__(**kwargs)

        self.set_action("load-set", self.load_set)
        self.set_action("next", self.select_next)
        self.set_action("down", self.select_down)
        self.set_action("previous", self.select_previous)
        self.set_action("up", self.select_up)
        self.set_action("mark", self.mark_current)
        self.set_action("mark-all", self.mark_all)
        self.set_action("mark-invert", self.mark_invert)

    def get_name(self):
        return "browser"

    def build_config(self, config):
        Component.build_config(self, config)

        config.add_section(self.get_name())

        section = self.get_config_hotkeys_section()
        config.add_section(section)
        config.set(section, "next", "275")
        config.set(section, "previous", "276")
        config.set(section, "down", "274")  # down arrow
        config.set(section, "up", "273")  # up arrow
        config.set(section, "mark", "32")  # space
        config.set(section, "switch-view viewer", "13")  # enter
        config.set(section, "mark-all", "97")  # a
        config.set(section, "mark-invert", "105")  # i

    def ready(self):
        Component.ready(self)
        self.session = self.get_app().lookup("session", "Entity")
        self.cursor = self.session.cursor

    def on_switch(self):
        self.cursor.bind(id=self.on_id_change)
        self.load_set()
        if self.selected_image != None:
            Clock.schedule_once(self.scroll_to_image)

    def on_switch_lose_focus(self):
        self.cursor.unbind(id=self.on_id_change)

    def scroll_to_image(self, dt):
        self.ids.scroll_view.scroll_to(self.selected_image)

    def load_set(self):
        self.grid.clear_widgets()

        if self.cursor.id == None:
            return

        threading.Thread(target=self._load_set_thread).start()

    def _load_set_thread(self):
        self.start_progress("Loading thumbs...")

        max_count = self.max_rows * self.grid.cols
        self.set_progress_max_count(max_count)
        self.reset_progress()

        self.page_cursor = self.cursor.get_cursor_by_pos(max(0, self.cursor.pos - max_count / 2))

        c = self.cursor.get_cursor_by_pos(self.page_cursor.pos)
        self.append_queue=True

        count = 0
        for i in range(max_count):
            filename = c.filename
            name = os.path.basename(filename)
            if len(name) > 12:
                name = name[:5] + "..." + name[-7:]
            thumb_data = c.get_thumbnail()

            self.image_queue.append((thumb_data, name, c.id, c.pos))

            count += 1
            if count >= max_count or not c.go_next():
                break

        self.pending_actions.append(self._load_process)
        self.do_next_action()

    def select_next(self):
        self.cursor.go_next()

    def select_down(self):
        if not self.select_row(1):
            self.cursor.go_last()

    def select_up(self):
        if not self.select_row(-1):
            self.cursor.go_first()
            print self.cursor.pos

    def select_row(self, diff):
        pos = self.cursor.pos - self.page_cursor.pos

        linenr = pos / self.grid.cols
        colnr = pos % self.grid.cols
        new_pos = colnr + (linenr + diff) * self.grid.cols
        return self.cursor.go(self.page_cursor.pos + new_pos)

    def select_previous(self):
        self.cursor.go_previous()

    def on_id_change(self, instance, value):
        if self.cursor.filename is None or self.cursor.filename == '' or value == None:
            if self.selected_image != None:
                self.selected_image.img.selected = False
            self.selected_image = None
        else:
            thumbs = [image for image in self.grid.children if image.id == value]
            if len(thumbs) > 0:
                if self.selected_image != None:
                    self.selected_image.img.selected = False
                thumb = thumbs[0]
                thumb.img.selected = True
                self.selected_image = thumb
                self.ids.scroll_view.scroll_to(thumb)
            else:
                if self.cursor.pos > self.grid.children[0].position:
                    self.cursor.go(self.grid.children[0].position)
                else:
                    self.cursor.go(self.page_cursor.pos)

    def on_image_touch_up(self, img):
        # select item
        self.cursor.go(img.id)

    def mark_current(self, value=None):
        self.cursor.mark(value)

    def mark_all(self, value=None):
        self.get_app().root.execute_cmd("mark-all", value)

    def mark_invert(self):
        self.get_app().root.execute_cmd("invert-mark")

    def load_more_next(self):
        if len(self.grid.children) == 0:
            self.do_next_action()
            return

        self.widget_to_scroll=self.grid.children[0]
        last_pos = self.grid.children[0].position
        c = self.cursor.get_cursor_by_pos(last_pos)

        max_count = self.page_rows * self.grid.cols

        self.image_queue.clear()
        self.append_queue = True
        self.start_progress("loading next images...")
        self.set_progress_max_count(max_count)

        for i in range(max_count):
            if not c.go_next():
                break

            filename = c.filename
            name = os.path.basename(filename)
            if len(name) > 12:
                name = name[:5] + "..." + name[-7:]
            thumb_data = c.get_thumbnail()
            self.image_queue.append((thumb_data, name, c.id, c.pos))


        if len(self.image_queue) > 0:
            self.pending_actions.append(self._load_process)
            self.pending_actions.append(self._remove_firsts)
            self.pending_actions.append(self._scroll_on_widget)
            self.do_next_action()
        else:
            self.stop_progress()

    def load_more_previous(self):
        if len(self.grid.children) == 0:
            self.do_next_action()
            return

        self.widget_to_scroll=self.grid.children[-1]
        c = self.cursor.get_cursor_by_pos(self.widget_to_scroll.position)
        max_count = self.page_rows * self.grid.cols

        self.image_queue.clear()
        self.append_queue = False
        self.set_progress_max_count(max_count)

        for i in range(max_count):
            if not c.go_previous():
                break

            filename = c.filename
            name = os.path.basename(filename)
            if len(name) > 12:
                name = name[:5] + "..." + name[-7:]
            thumb_data = c.get_thumbnail()
            self.image_queue.append((thumb_data, name, c.id, c.pos))


        if len(self.image_queue) > 0:
            self.start_progress("loading previous images...")
            self.pending_actions.append(self._load_process)
            self.pending_actions.append(self._remove_lasts)
            self.pending_actions.append(self._scroll_on_widget)
            self.do_next_action()
        else:
            self.stop_progress()

    def _load_process(self, dt):
        if len(self.image_queue) > 0:
            for i in range(min(len(self.image_queue), self.grid.cols)):
                data, name, id, pos = self.image_queue.popleft()

                image = Thumb(data=data, cell_size=self.cell_size, caption=name, selected=id == self.cursor.id)
                draggable = Item(img=image, container=self, cell_size=self.cell_size, id=id, position=pos)
                if image.selected:
                    self.selected_image = draggable

                if self.append_queue:
                    self.grid.add_widget(draggable)
                else:
                    self.grid.add_widget(draggable, len(self.grid.children))
                self.tick_progress()
            Clock.schedule_once(self._load_process, 0)
        else:
            self.stop_progress()
            self.do_next_action()

    def do_next_action(self):
        if len(self.pending_actions)>0:
            action=self.pending_actions.popleft()
            Clock.schedule_once(action)

    def _remove_firsts(self,dt):
        child_count=len(self.grid.children)
        to_remove=child_count-(self.max_rows*self.grid.cols)
        if to_remove>0:
            for i in range(to_remove):
                widget=self.grid.children[-1]
                self.grid.remove_widget(widget)

            widget = self.grid.children[-1]
            self.page_cursor.go(widget.position)
            if self.cursor.pos<self.page_cursor.pos:
                self.cursor.go(self.grid.children[0].position)
        self.do_next_action()

    def _remove_lasts(self,dt):
        child_count=len(self.grid.children)
        to_remove=child_count-(self.max_rows*self.grid.cols)
        if to_remove>0:
            for i in range(to_remove):
                widget=self.grid.children[0]
                self.grid.remove_widget(widget)

            widget = self.grid.children[-1]
            self.page_cursor.go(widget.position)
            if self.cursor.pos>self.grid.children[0].position:
                self.cursor.go(self.grid.children[-1].position)

        self.do_next_action()

    def _scroll_on_widget(self,dt):
        if self.widget_to_scroll is not None:
            # self.ids.scroll_view.scroll_to(self.widget_to_scroll)
            self.widget_to_scroll=None
        self.do_next_action()