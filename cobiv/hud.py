from kivy.properties import BooleanProperty
from kivy.uix.relativelayout import RelativeLayout


class HUD(RelativeLayout):
    visible = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(HUD, self).__init__(**kwargs)
        pass
