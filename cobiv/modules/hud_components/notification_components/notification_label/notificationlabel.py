from kivy.animation import Animation
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.label import Label

from modules.core.hud import Hud

Builder.load_string('''
<NotificationLabel>:
    size_hint: None, None
    size: self.texture_size
''')


class NotificationLabel(Hud, Label):
    def __init__(self, key=None, error=False, **kwargs):
        super().__init__(pos=(5, 1), **kwargs)
        self.color = self.get_config_value("error_color", (0.6, 0, 0, 1)) if error else self.get_config_value("color", (
            1, 1, 1, 1))
        self.outline_color = self.get_config_value("outline_color", (0, 0, 0, 1))
        self.outline_width = self.get_config_value("outline_width", 1)
        self.font_size = self.get_config_value("font_size", "40sp")

        blended_color = (self.color[0], self.color[1], self.color[2], 0)
        anim = Animation(y=self.get_config_value("distance", 200), color=blended_color,
                         duration=self.get_config_value("duration", 2.))
        anim.bind(on_complete=lambda instance, value: self.parent.on_notification_complete(key, self))
        anim.start(self)

    def update(self, text=None, **kwargs):
        if text is not None:
            self.text = text

    def get_name(self=None):
        return "NotificationLabel"


Factory.register("NotificationLabel", NotificationLabel)
