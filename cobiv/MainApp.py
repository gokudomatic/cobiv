import os

import logging


logging.basicConfig(level=logging.DEBUG)

from cobiv.MainContainer import MainContainer

import kivy
import yaml
from kivy.app import App
from kivy.lang import Builder
from yapsy.PluginManager import PluginManager

from cobiv.modules.core.entity import Entity
from cobiv.modules.core.hud import Hud
from cobiv.modules.core.view import View
from cobiv.modules.database.datasources.datasource import Datasource
from cobiv.modules.io.reader.tagreader import TagReader
from cobiv.modules.core.book.book_manager import BookManager
from cobiv.modules.core.gestures.gesture import Gesture
from cobiv.modules.core.sets.setmanager import SetManager

kivy.require('1.9.1')

Builder.load_file('main.kv')


class Cobiv(App):
    root = None
    observers={}

    logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(Cobiv, self).__init__(**kwargs)
        self.plugin_manager = PluginManager()
        self.plugin_manager.setPluginPlaces(["modules"])
        self.plugin_manager.setCategoriesFilter({
            "View": View,
            "Entity": Entity,
            "Hud": Hud,
            "TagReader": TagReader,
            "Datasource": Datasource,
            "SetManager": SetManager,
            "BookManager": BookManager,
            "Gesture": Gesture
        })

        self.plugin_manager.locatePlugins()
        self.plugin_manager.loadPlugins()

        for plugin in self.plugin_manager.getAllPlugins():
            print("Plugin found : {} {} {}".format(plugin.plugin_object,plugin.name,plugin.categories))

        config_path=os.path.join(os.path.expanduser('~'),'.cobiv')
        if not os.path.exists(config_path):
            os.makedirs(config_path)

    def build_yaml_config(self):
        if not os.path.exists('cobiv.yml'):
            f=open('cobiv.yml', 'w')
            data=self.root.build_yaml_main_config()
            for plugin in self.plugin_manager.getAllPlugins():
                plugin.plugin_object.build_yaml_config(data)
            yaml.dump(data,f)
            f.close()
        f=open('cobiv.yml')
        config=yaml.safe_load(f)
        f.close()
        self.root.configuration=config
        self.root.read_yaml_main_config(config)
        for plugin in self.plugin_manager.getAllPlugins():
            plugin.plugin_object.read_yaml_config(config)

    def build(self):
        self.root = MainContainer()

        for plugin in self.plugin_manager.getPluginsOfCategory("View"):
            self.root.available_views[plugin.plugin_object.get_name()] = plugin.plugin_object

        self.build_yaml_config()

        print("----------------------------------------------")

        for plugin in self.plugin_manager.getAllPlugins():
            plugin.plugin_object.ready()
            print("plugin ready : "+str(plugin.name))
            self.logger.debug("plugin ready : "+str(plugin.name))

        self.root.switch_view(self.get_config_value('startview','help'))

        self.root.ready()

        return self.root

    def on_stop(self):
        for plugin in self.plugin_manager.getAllPlugins():
            plugin.plugin_object.on_application_quit()

    def lookup(self, name, category):
        plugin=self.plugin_manager.getPluginByName(name, category=category)
        return plugin.plugin_object if plugin is not None else None

    def lookups(self,category):
        return [plugin.plugin_object for plugin in self.plugin_manager.getPluginsOfCategory(category)]

    def register_event_observer(self,evt_name,callback):
        if not evt_name in self.observers:
            self.observers[evt_name]=[callback]
        else:
            self.observers[evt_name].append(callback)

    def fire_event(self,evt_name,*args,**kwargs):
        if evt_name in self.observers:
            for callback in self.observers[evt_name]:
                callback(*args,**kwargs)

    def get_user_path(self,*args):
        return os.path.join(os.path.expanduser('~'),'.cobiv',*args)

    def get_config_value(self,key,default=None):
        keys=key.split('.')
        cfg=self.root.configuration
        for k in keys:
            if k in cfg:
                cfg=cfg.get(k)
            else:
                return default
        return cfg

if __name__ == '__main__':
    Cobiv().run()
