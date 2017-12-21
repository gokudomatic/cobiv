import os
from kivy.app import App


class AbstractApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.configuration = {}

        self.observers={}

    def get_config_value(self, key, defaultValue=""):
        if key in self.configuration:
            return self.configuration[key]
        else:
            return defaultValue


    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    def fire_event(self, evt_name, *args, **kwargs):
        if evt_name in self.observers:
            for callback in self.observers[evt_name]:
                callback(*args,**kwargs)

    def clear_observers(self):
        self.observers={}

    def lookups(self, category):
        return []

    def lookup(self,name,category):
        return None

    def register_event_observer(self,evt_name,callback):
        if not evt_name in self.observers:
            self.observers[evt_name]=[callback]
        else:
            self.observers[evt_name].append(callback)
