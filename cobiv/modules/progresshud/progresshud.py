from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from cobiv.modules.hud import Hud


Builder.load_file('modules/progresshud/progresshud.kv')
from cobiv.modules.view import View


class ProgressHud(Hud,AnchorLayout):

    value=NumericProperty(0)

    def __init__(self,**kwargs):
         super(ProgressHud,self).__init__(**kwargs)
