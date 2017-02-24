import os

from kivy.lang import Builder
from kivy.uix.rst import RstDocument

from cobiv.modules.view import *

Builder.load_file('modules/help/help.kv')


class HelpView(View, RstDocument):
    def __init__(self, **kwargs):
        super(HelpView, self).__init__(**kwargs)
        with open(os.path.join("modules/help", "help.rst")) as stream:
            self.text = stream.read()

        self.set_action("up",self.cmd_scroll_up)
        self.set_action("down",self.cmd_scroll_down)

    def get_name(instance=None):
        return "help"

    def cmd_scroll_up(self,dist=20):
        self._cmd_scroll(True,dist)

    def cmd_scroll_down(self,dist=20):
        self._cmd_scroll(False,dist)

    def _cmd_scroll(self, up=False, dist=20):
        d=int(dist)
        (dx, dy) = self.convert_distance_to_scroll(0, d * (1 if up else -1))
        self.scroll_y += dy

    def build_config(self,config):
        Component.build_config(self,config)
        section=self.get_config_hotkeys_section()
        config.add_section(section)
        config.set(section, "up 20", "273")  # up arrow
        config.set(section, "down 20", "274")  # down arrow
