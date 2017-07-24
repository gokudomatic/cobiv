from kivy.app import App
from yapsy.IPlugin import IPlugin

from cobiv.common import set_action, set_hotkey


class Component(object):
    _progress_max_count = 100
    _progress_count = 0

    def build_config(config):
        pass

    def set_action(self, name, fn):
        set_action(name, fn, self.get_name())

    def set_hotkey(self, key, command, modifier=0):
        set_hotkey(key, command, modifier, self.get_name())

    def get_name(self=None):
        return ""

    def get_config_hotkeys_section(self):
        return self.get_name() + "_hotkeys"

    def build_config(self, config):
        pass

    def ready(self):
        pass

    def get_app(self):
        return App.get_running_app()

    def get_global_config_value(self, key, default=None):
        return App.get_running_app().get_config_value(key, default)

    def get_config_value(self, key, default=None):
        return self.get_global_config_value(self.get_name() + '.' + key, default)

    def on_application_quit(self):
        pass

    def build_yaml_config(self, config):
        return config

    def read_yaml_config(self, config):
        if config.has_key(self.get_name()):
            for hotkey_config in config[self.get_name()].get('hotkeys', []):
                set_hotkey(long(hotkey_config['key']), hotkey_config['binding'], hotkey_config.get('modifiers', 0),
                           self.get_name())

    def start_progress(self, caption=None):
        self.get_app().root.show_progressbar()
        self.get_app().root.set_progressbar_value(0, caption=caption)
        self._progress_count = 0

    def set_progress(self, value, caption=None):
        self.get_app().root.set_progressbar_value(value, caption=caption)

    def set_progress_caption(self, caption):
        self.get_app().root.set_progressbar_caption(caption)

    def stop_progress(self):
        self.get_app().root.close_progressbar()

    def set_progress_max_count(self, value):
        self._progress_max_count = value

    def reset_progress(self, caption=None):
        self._progress_count = 0
        self.set_progress(0, caption)

    def tick_progress(self, caption=None, size=1):
        self._progress_count += size
        self.set_progress(self._progress_count * 100 / self._progress_max_count, caption)

    def notify(self, message, is_error=False):
        self.get_app().root.notify(message, is_error=is_error)

    def execute_cmd(self,cmd, force_default=False):
        self.get_app().root.execute_cmd(cmd,force_default=force_default)