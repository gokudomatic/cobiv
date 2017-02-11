from cobiv.common import *


class View:
    def get_name(instance=None):
        pass

    def set_action(self, name, fn):
        set_action(name, fn, self.get_name())

    def set_hotkey(self, key, command, modifier=0):
        set_hotkey(key, command, modifier, self.get_name())
