import os

from kivy.app import App
from kivy.core.window import Window
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.factory import Factory
from kivy.vector import Vector

from cobiv.modules.core.component import Component
from kivy.lang import Builder
from kivy.properties import ObjectProperty, Clock
from kivy.uix.scrollview import ScrollView

from cobiv.modules.core.imageset.slide import SlideMode, Slide
from cobiv.modules.core.view import View

Builder.load_file(os.path.abspath(os.path.join(os.path.dirname(__file__), 'viewer.kv')))


class HorizontalSidebarEffect(DampedScrollEffect):
    overscroll_limit = 50

    def __init__(self, **kwargs):
        super(HorizontalSidebarEffect, self).__init__(**kwargs)
        self.trigger_navigate_right = Clock.create_trigger(lambda dt: self.navigate(True), 0.5)
        self.trigger_navigate_left = Clock.create_trigger(lambda dt: self.navigate(False), 0.5)

    def on_overscroll(self, *args):
        super(HorizontalSidebarEffect, self).on_overscroll(*args)
        if self.overscroll < -self.overscroll_limit:
            self.trigger_navigate_right()
        elif self.overscroll > self.overscroll_limit:
            self.trigger_navigate_left()

    def navigate(self, go_right):
        if go_right:
            App.get_running_app().root.get_view().load_next()
        else:
            App.get_running_app().root.get_view().load_previous()


class Viewer(View, ScrollView):
    fit_mode = ObjectProperty(SlideMode.FIT_SCREEN)
    session = None
    cursor = None

    swipe_event = None
    swipe_frequency = 0
    swipe_direction = 0

    def __init__(self, **kwargs):
        super(Viewer, self).__init__(**kwargs)

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
        self.set_action("mark", self.mark)
        self.set_action("is-marked", self.print_mark)
        self.set_action("refresh-marked", self.refresh_marked)

    def build_yaml_config(self, config):
        config[self.get_name()] = {
            'hotkeys': [
                {'key': '13', 'binding': 'switch-view browser'},
                {'key': '273', 'binding': 'up 20'},
                {'key': '274', 'binding': 'down 20'},
                {'key': '275', 'binding': 'next'},
                {'key': '276', 'binding': 'previous'},
                {'key': '103', 'binding': 'first'},
                {'key': '103', 'binding': 'last', 'modifiers': '1'},
                {'key': '105', 'binding': 'scroll-up'},
                {'key': '107', 'binding': 'scroll-down'},
                {'key': '106', 'binding': 'scroll-left'},
                {'key': '108', 'binding': 'scroll-right'},
                {'key': '48', 'binding': 'zoom-in'},
                {'key': '57', 'binding': 'zoom-out'}
            ]
        }
        return config

    def ready(self):
        Component.ready(self)
        self.session = self.get_session()
        self.cursor = self.session.cursor
        app = self.get_app()
        app.register_event_observer('on_gesture_pinch', self.on_pinch)
        app.register_event_observer('on_gesture_swipe', self.on_swipe)
        app.register_event_observer('on_stop_gesture_swipe', self.on_stop_swipe)

    def on_switch(self):
        self.cursor.bind(filename=self.on_cursor_change)
        self.load_set()

    def on_switch_lose_focus(self):
        self.cursor.unbind(filename=self.on_cursor_change)

    def load_set(self):
        self.load_slide()

    def on_cursor_change(self, instance, value):
        self.load_slide()

    def load_slide(self):
        if self.cursor.implementation is None:
            return

        file_type = self.cursor.get_tag(0, 'file_type', 0)
        if self.cursor.filename is None:
            image = None
        else:
            default_slide_classname = 'Slide'
            if file_type == 'book':
                default_slide_classname = 'BookSlide'
            slide_classname = self.get_config_value(key='slide.classmap.' + file_type,
                                                    default=default_slide_classname)

            image_class = Factory.get(slide_classname)
            image = image_class(session=self.session, load_mode=self.fit_mode, cursor=self.cursor)

        self.clear_widgets()
        if image:
            self.add_widget(image)

        self.show_status(key="viewer_load", renderer="ActionStatusMeter",
                         value=self.session.fields['currentset_position'](),
                         max_value=self.session.fields['currentset_count'](),
                         pos_hint={'center_x': 0.5, 'center_y': 0.5}, size_hint=(0.5, None))

    def load_next(self):
        if not self.cursor.go_next():
            self.cursor.go_first()

    def load_previous(self):
        if not self.cursor.go_previous():
            self.cursor.go_last()

    def load_first(self):
        self.cursor.go_first()

    def count(self):
        return len(self.cursor)

    def jump_to_slide(self, value):
        self.cursor.go(value)

    def load_last(self):
        self.cursor.go_last()

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
        print("zoom before : {}".format(self.children[0].zoom))
        self._set_zoom(1 + 0.05)
        print("zoom after : {}".format(self.children[0].zoom))

    def zoom_out(self):
        print("zoom before : {}".format(self.children[0].zoom))
        self._set_zoom(1 - 0.05)
        print("zoom after : {}".format(self.children[0].zoom))

    def zoom_1(self):
        self._set_fit_mode(SlideMode.NORMAL)
        self.children[0].zoom = 1

    def _set_zoom(self, factor, center=None):
        self._set_fit_mode(SlideMode.NORMAL)

        image = self.children[0]

        if center is None:
            center = (Window.width / 2, Window.height / 2)

        sv0 = Vector((image.width - Window.width) * self.scroll_x, (image.height - Window.height) * self.scroll_y)
        cv = Vector(image.to_widget(*center))

        sv1 = sv0 + cv * (factor - 1)
        image.zoom *= factor

        self.show_status(key="viewer_zoom", renderer="ActionStatusLabel", text="{:.2f}%".format(image.zoom * 100),
                         pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.scroll_x, self.scroll_y = self.convert_distance_to_scroll(sv1.x, sv1.y)

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

    def mark(self):
        self.cursor.mark()

    def print_mark(self):
        is_marked = self.cursor.get_mark()
        self.notify(str(is_marked))

    def refresh_marked(self):
        pass

    def remove_slide(self):
        if self.cursor.remove():
            self.load_slide()
            # TODO when rm and go previous, nothing happens

    def _get_image(self):
        return self.children[0]

    def on_pinch(self, amount, center):

        fac = 0.005
        self._set_zoom(fac * amount - fac + 1, center)

    def on_swipe(self, vector, origin):
        v = vector.normalize()
        if abs(v.y) < 0.5:
            frequency = vector.length()

            if self.swipe_event is None or abs(self.swipe_frequency - frequency) > 100:
                if self.swipe_event is not None:
                    self.swipe_event.cancel()
                self.swipe_event = Clock.schedule_interval(self.swipe_callback, 100 / frequency)
                self.swipe_frequency = frequency
                self.swipe_direction = (v.x > 0)
        elif self.swipe_event is not None:
            self.on_stop_swipe()
        else:
            self.swipe_callback(0)

    def on_stop_swipe(self):
        if self.swipe_event is not None:
            self.swipe_event.cancel()
            self.swipe_frequency = 0
            self.swipe_event = None
            self.swipe_callback(0)

    def swipe_callback(self, dt):
        if self.swipe_direction:
            self.load_previous()
        else:
            self.load_next()
