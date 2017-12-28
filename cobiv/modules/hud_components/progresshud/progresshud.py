import os
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout

from cobiv.modules.core.hud import Hud

Builder.load_file(os.path.abspath(os.path.join(os.path.dirname(__file__), 'progresshud.kv')))


class ProgressHud(Hud, AnchorLayout):
    value = NumericProperty(0)
    caption = StringProperty("")

    def __init__(self, **kwargs):
        super(ProgressHud, self).__init__(**kwargs)
