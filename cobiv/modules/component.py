from kivy.app import App
from yapsy.IPlugin import IPlugin

from cobiv.common import set_action, set_hotkey


class Component():
    def build_config(config):
        pass

    def set_action(self, name, fn):
        set_action(name, fn, self.get_name())

    def set_hotkey(self, key, command, modifier=0):
        set_hotkey(key, command, modifier, self.get_name())

    def get_name(self=None):
        return ""

    def get_config_hotkeys_section(self):
        return self.get_name()+"_hotkeys"

    def build_config(self,config):
        pass

    def ready(self):
        pass

    def get_app(self):
        return App.get_running_app()

    def read_config(self):
        config = self.get_app().config
        if config.has_section(self.get_config_hotkeys_section()):

            for binding, value in config.items(self.get_config_hotkeys_section()):
                if "/" in value:
                    b = value.split("/")
                    set_hotkey(long(b[0]), binding, modifier=int(b[1]),profile=self.get_name())
                else:
                    set_hotkey(long(value), binding,profile=self.get_name())
