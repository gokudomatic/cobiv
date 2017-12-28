from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, Clock
from kivy.uix.widget import Widget

from cobiv.modules.core.component import Component

Builder.load_string('''
<TouchButton>:
    rad: self.rad_large if self.active else self.rad_small
    canvas:
        Color:
            rgba: 1,0,0,0.8 if self.active else 0.4
        Ellipse:
            pos: self.x-self.width/2,self.y-self.height/2
            size: self.size
    size_hint: None, None
    size: self.rad, self.rad
''')


class TouchButton(Component, Widget):
    rad_small = NumericProperty(50)
    rad_large = NumericProperty(150)
    rad = NumericProperty(None)
    active = BooleanProperty(False)
    visible = BooleanProperty(None)

    def __init__(self, **kwargs):
        super(TouchButton, self).__init__(**kwargs)
        self.trigger = Clock.create_trigger(self.on_toggle, 0.1)
        self.bind(visible=self.on_toggle_visible)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.trigger()
            return True
        else:
            return super(TouchButton, self).on_touch_down(touch)

    def on_toggle(self, dt):
        self.active = not self.active

    def collide_point(self, x, y):
        return (x - self.x) ** 2 + (y - self.y) ** 2 <= self.rad ** 2

    def ready(self):
        self.rad_small = self.get_config_value('gestures.switcher.inactive_size', 50)
        self.rad_large = self.get_config_value('gestures.switcher.active_size', 150)
        self.visible = self.get_config_value('gestures.switcher.visible', True)
        # if self.get_config_value('gestures.switcher.visible', True):
        #     self.pos = self.get_config_value('gestures.switcher.pos', {"x": 0.5, "y": 1})
        #     print(self.pos)
        # else:
        #     self.pos = {"x": -1000, "y": -1000}

    def on_toggle_visible(self, instance, value):
        if value:
            self.pos_hint = self.get_config_value('gestures.switcher.pos', {"x": 0.5, "y": 1})
        else:
            self.pos_hint = {"x": -1000, "y": -1000}
