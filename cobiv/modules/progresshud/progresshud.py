from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout

from cobiv.modules.hud import Hud


Builder.load_file('modules/progresshud/progresshud.kv')


class ProgressHud(Hud,AnchorLayout):

    value=NumericProperty(0)
    caption=StringProperty("")

    def __init__(self,**kwargs):
         super(ProgressHud,self).__init__(**kwargs)
