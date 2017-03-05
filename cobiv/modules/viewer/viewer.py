from kivy.lang import Builder
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.scrollview import ScrollView

from cobiv.modules.component import Component
from cobiv.modules.entity import Entity
from cobiv.modules.imageset.ImageSet import SlideMode
from cobiv.modules.view import View

Builder.load_file('modules/viewer/viewer.kv')


class Viewer(View, ScrollView):
    fit_mode = ObjectProperty(SlideMode.FIT_SCREEN)
    slide_index = NumericProperty(-1)
    current_imageset = None
    slide_cache = {}
    session = None

    def __init__(self, **kwargs):
        super(Viewer, self).__init__(**kwargs)

        self.bind(slide_index=self.load_slide)

        self.set_action("scroll-up", self.scroll_up)
        self.set_action("scroll-down", self.scroll_down)
        self.set_action("scroll-left", self.scroll_left)
        self.set_action("scroll-right", self.scroll_right)

        self.set_action("rm", self.remove_slide)
        self.set_action("load-set", self.load_set)

        self.set_action("zoom-in", self.zoom_in)
        self.set_action("zoom-out", self.zoom_out)
        self.set_action("zoom-1", self.zoom_1)
        self.set_action("fit-width", self.fit_width)
        self.set_action("fit-height", self.fit_height)
        self.set_action("fit-screen", self.fit_screen)
        self.set_action("go", self.jump_to_slide)
        self.set_action("next", self.load_next)
        self.set_action("previous", self.load_previous)
        self.set_action("first", self.load_first)
        self.set_action("last", self.load_last)

    def build_config(self, config):
        Component.build_config(self, config)
        section = self.get_config_hotkeys_section()
        config.add_section(section)
        config.set(section, "up 20", "273")  # up arrow
        config.set(section, "down 20", "274")  # down arrow
        config.set(section, "next", "275")
        config.set(section, "previous", "276")
        config.set(section, "first", "103")
        config.set(section, "last", "103/1")
        config.set(section, "scroll-up", "105", )
        config.set(section, "scroll-down", "107")
        config.set(section, "scroll-left", "106")
        config.set(section, "scroll-right", "108")
        config.set(section, "zoom-in", "48")
        config.set(section, "zoom-out", "57")

    def ready(self):
        Component.ready(self)
        self.session=self.get_app().lookup("session", "Entity")
        self.current_imageset = self.session.get_currentset()

        self.slide_index = 0

    def on_switch(self):
        self.load_set()

    def load_set(self):
        self.slide_cache.clear()
        self.slide_index = -1
        self.slide_index = self.session.current_imageset_index

    def load_slide(self, instance, value):
        if value == -1:
            return

        image = False
        if self.current_imageset != None and len(self.current_imageset) > 0:
            if 0 <= value < self.count():
                filename = self.current_imageset.uris[value]
                self.current_imageset.current = [filename]
                if self.slide_cache.has_key(filename):
                    image = self.slide_cache[filename]
                else:
                    image = self.current_imageset.image(value, self.fit_mode)
                    self.slide_cache[filename] = image

        self.clear_widgets()
        if image:
            self.add_widget(image)

        self.session.current_imageset_index=value

    def load_next(self):
        self.slide_index = self.current_imageset.next(self.slide_index)

    def load_previous(self):
        self.slide_index = self.current_imageset.previous(self.slide_index)

    def load_first(self):
        self.slide_index = 0

    def count(self):
        return len(self.current_imageset.uris)

    def jump_to_slide(self, value):
        self.slide_index = int(value) % self.count()

    def load_last(self):
        self.slide_index = len(self.current_imageset.uris) - 1

    def get_name(instance=None):
        return "viewer"

    def scroll_up(self):
        self._cmd_scroll_y(True, dist=10)

    def scroll_down(self):
        self._cmd_scroll_y(dist=10)

    def scroll_left(self):
        self._cmd_scroll_x(True, dist=10)

    def scroll_right(self):
        self._cmd_scroll_x(dist=10)

    def _cmd_scroll_y(self, up=False, dist=20):
        d = int(dist)
        (dx, dy) = self.convert_distance_to_scroll(0, d * (1 if up else -1))
        self.scroll_y += dy
        self.update_from_scroll()

    def _cmd_scroll_x(self, left=False, dist=20):
        d = int(dist)
        (dx, dy) = self.convert_distance_to_scroll(d * (1 if not left else -1), 0)
        self.scroll_x += dx
        self.update_from_scroll()

    def zoom_in(self):
        self._set_fit_mode(SlideMode.NORMAL)
        self._set_zoom(0.05)

    def zoom_out(self):
        self._set_fit_mode(SlideMode.NORMAL)
        self._set_zoom(-0.05)

    def zoom_1(self):
        self._set_fit_mode(SlideMode.NORMAL)
        self.children[0].zoom = 1

    def _set_zoom(self, factor):
        self.children[0].zoom += factor

    def fit_width(self):
        self._set_fit_mode(SlideMode.FIT_WIDTH)

    def fit_height(self):
        self._set_fit_mode(SlideMode.FIT_HEIGHT)

    def fit_screen(self):
        self._set_fit_mode(SlideMode.FIT_SCREEN)

    def _set_fit_mode(self, mode):
        self.fit_mode = mode
        self.children[0].mode = mode
        self.update_from_scroll()

    def remove_slide(self):
        old_idx = self.slide_index
        self.slide_index = self.current_imageset.remove(self.slide_index)
        if self.slide_index > 0 or old_idx == 0:
            self.load_slide(self, self.slide_index)
