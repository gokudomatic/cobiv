from kivy.animation import Animation
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.label import Label

from cobiv.modules.core.hud import Hud

Builder.load_string('''
<ActionStatusLabel>:
    size_hint: None, None
    size: self.texture_size
''')


class ActionStatusLabel(Hud, Label):
    def __init__(self, key=None, **kwargs):
        super().__init__(**kwargs)

        self.color = self.get_config_value("color", (1, 1, 1, 1))
        self.outline_color = self.get_config_value("outline_color", (0, 0, 0, 1))
        self.outline_width = self.get_config_value("outline_width", 1)
        self.font_size = self.get_config_value("font_size", "60sp")
        self.key = key
        self.anim = None

    def start(self):
        if self.parent is not None:
            self.reset_animation()

    def update(self, text=None, **kwargs):
        if text is not None:
            self.text = text
            self.reset_animation()

    def reset_animation(self):
        if self.anim is not None:
            self.anim.cancel(self)
            self.color = (self.color[0], self.color[1], self.color[2], 1)
        self.anim = Animation(duration=1.) + Animation(color=(self.color[0], self.color[1], self.color[2], 0),
                                                       duration=self.get_config_value("duration", 0.5))
        self.anim.bind(on_complete=lambda instance, value: self.parent.on_notification_complete(self.key, self))
        self.anim.start(self)

    def get_name(self=None):
        return "ActionStatusLabel"


Factory.register("ActionStatusLabel", ActionStatusLabel)
