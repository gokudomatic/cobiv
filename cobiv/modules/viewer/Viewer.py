from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.carousel import Carousel
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.scrollview import ScrollView

from cobiv.modules.imageset.ImageSet import current_imageset
from cobiv.modules.view import *

Builder.load_file('modules/viewer/viewer.kv')


class Viewer(View, Carousel):
    def __init__(self, **kwargs):
        super(Viewer, self).__init__(**kwargs)
        self.anim_move_duration=0.1

        self.load_imageset()

        self.set_action("next",self.load_next)
        self.set_action("previous",self.load_previous)
        self.set_action("first",self.load_first)

        self.set_hotkey(275,"next")
        self.set_hotkey(108L,"next")
        self.set_hotkey(106L,"previous")
        self.set_hotkey(276,"previous")
        self.set_hotkey(103L,"first")

    def load_imageset(self,imageset=current_imageset):
        self.clear_widgets()
        for i in imageset.images():
            scatter=ScatterLayout(do_rotation=False)
            scatter.add_widget(i)
            self.add_widget(scatter)

    def load_first(self):
        self.load_slide(self.slides[0])

    @staticmethod
    def get_name(instance=None):
        return "viewer"

available_views[Viewer.get_name()] = Viewer
