from kivy.lang import Builder
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.scrollview import ScrollView

from cobiv.modules.imageset.ImageSet import current_imageset, SlideMode
from cobiv.modules.view import *

Builder.load_file('modules/viewer/viewer.kv')


class Viewer(View, ScrollView):
    fit_mode = ObjectProperty(SlideMode.FIT_SCREEN)
    slide_index = NumericProperty(None)

    slide_cache = {}

    def __init__(self, **kwargs):
        super(Viewer, self).__init__(**kwargs)

        self.bind(slide_index=self.load_slide)

        self.slide_index = 0

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
        self.set_hotkey(275, "next")
        self.set_hotkey(276, "previous")
        self.set_hotkey(103L, "first")
        self.set_hotkey(103L, "last", 1)
        self.set_hotkey(105L, "scroll-up")
        self.set_hotkey(107L, "scroll-down")
        self.set_hotkey(106L, "scroll-left")
        self.set_hotkey(108L, "scroll-right")
        self.set_hotkey(48L, "zoom-in")
        self.set_hotkey(57L, "zoom-out")

    def load_set(self):
        self.slide_cache.clear()
        self.slide_index = -1
        self.slide_index = 0

    def load_slide(self, instance, value):
        if value<0:
            return

        image=False
        if current_imageset!=None and len(current_imageset.uris)>0:
            if 0<=value<self.count():
                filename=current_imageset.uris[value]
                current_imageset.current=[filename]
                if self.slide_cache.has_key(filename):
                    image = self.slide_cache[filename]
                    # image.mode = self.fit_mode
                else:
                    image = current_imageset.image(value, self.fit_mode)
                    self.slide_cache[filename] = image

        self.clear_widgets()
        if image:
            self.add_widget(image)

    def load_next(self):
        self.slide_index = current_imageset.next(self.slide_index)

    def load_previous(self):
        self.slide_index = current_imageset.previous(self.slide_index)

    def load_first(self):
        self.slide_index = 0

    def count(self):
        return len(current_imageset.uris)

    def jump_to_slide(self, value):
        self.slide_index = int(value) % self.count()

    def load_last(self):
        self.slide_index = len(current_imageset.uris) - 1

    @staticmethod
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
        old_idx=self.slide_index
        self.slide_index=current_imageset.remove(self.slide_index)
        if self.slide_index>0 or old_idx==0:
            self.load_slide(self,self.slide_index)

available_views[Viewer.get_name()] = Viewer
