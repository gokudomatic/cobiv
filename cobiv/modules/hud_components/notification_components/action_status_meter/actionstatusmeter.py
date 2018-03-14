from math import floor

from kivy.animation import Animation
from kivy.factory import Factory
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Line
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from modules.core.hud import Hud

Builder.load_string('''
<ActionMeterWidget>:

<ActionStatusMeter>:
    orientation: 'vertical'
    size_hint: None, None
    padding: 10
    canvas.before:
        Color:
            rgba: 0,0,0,0.3
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: '{} / {}'.format(root.value,root.max_value)
        font_size: root.font_size
    ActionMeterWidget:
        id: meter
        value: 0 if root.max_value==0 else root.value / root.max_value
''')



class ActionStatusMeter(Hud, BoxLayout):
    value = NumericProperty(0)
    max_value = NumericProperty(100)
    font_size = StringProperty('40sp')

    class ActionMeterWidget(Widget):

        value=NumericProperty(0)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.bind(pos=self.repaint, size=self.repaint, value=self.repaint)

        def repaint(self, *args):
            self.canvas.clear()
            w = 5
            with self.canvas:
                Color(1, 1, 1, 1)
                Line(points=(self.pos[0], self.pos[1], self.pos[0], self.pos[1] + self.height), width=w, cap='none')
                Line(
                    points=(self.pos[0] + self.width, self.pos[1], self.pos[0] + self.width, self.pos[1] + self.height),
                    width=w, cap='none')

                y = self.pos[1] + self.height / 2
                x = self.pos[0] + w * 2
                for i in range(floor(self.width / (4 * w))):
                    Line(points=(x + i * 4 * w, y, x + (i * 4 + 2) * w, y), width=w, cap='none')

                # cursor
                Color(1, 0, 0, 1)
                x = self.pos[0] + self.value * self.width
                y0 = self.pos[1] + 0.05 * self.height
                y1 = self.pos[1] + 0.95 * self.height
                Line(points=(x, y0, x, y1), width=w // 2, cap='none')

    def __init__(self, key=None, value=0, max_value=100, **kwargs):
        super().__init__(**kwargs)
        self.max_value = max_value
        self.value = value
        self.key=key
        self.font_size=self.get_config_value('font_size','40sp')
        self.anim = None
        self.reset_animation()

    def update(self, value=None, **kwargs):
        if value is not None:
            self.value=value
            self.reset_animation()

    def reset_animation(self):
        if self.anim is not None:
            self.anim.cancel(self)
            self.opacity=1
        self.anim = Animation(duration=1.) + Animation(opacity=0,
                                                       duration=self.get_config_value("duration", 0.5))
        self.anim.bind(on_complete=lambda instance, value: self.parent.on_notification_complete(self.key, self))
        self.anim.start(self)


    def get_name(self=None):
        return "ActionStatusMeter"


Factory.register("ActionStatusMeter", ActionStatusMeter)
