import kivy

from cobiv.modules.component import Component
from cobiv.modules.entity import Entity
from cobiv.modules.view import View

kivy.require('1.9.1')
from kivy.app import App
from MainContainer import MainContainer,build_main_config
from kivy.lang import Builder
from yapsy.PluginManager import PluginManager

Builder.load_file('main.kv')


class Cobiv(App):

    root=None


    def __init__(self, **kwargs):
        super(Cobiv, self).__init__(**kwargs)
        self.plugin_manager=PluginManager()
        self.plugin_manager.setPluginPlaces(["modules"])
        self.plugin_manager.setCategoriesFilter({
            "View":View,
            "Entity":Entity
        })
        self.plugin_manager.locatePlugins()
        self.plugin_manager.loadPlugins()

    def build_config(self, config):
        build_main_config(config)
        for plugin in self.plugin_manager.getAllPlugins():
            plugin.plugin_object.build_config(config)
            plugin.plugin_object.read_config()

    def build(self):
        self.root=MainContainer()

        for plugin in self.plugin_manager.getPluginsOfCategory("View"):
            self.root.available_views[plugin.plugin_object.get_name()]=plugin.plugin_object

        for plugin in self.plugin_manager.getAllPlugins():
            plugin.plugin_object.ready()

        self.root.switch_view("browser")

        return self.root

    def lookup(self,name,category):
        return self.plugin_manager.getPluginByName(name,category=category).plugin_object


if __name__ == '__main__':
    Cobiv().run()
