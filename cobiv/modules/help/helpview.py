import os

from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.uix.rst import RstDocument

from cobiv.modules.view import View
from cobiv.viewlist import available_views

Builder.load_file('modules/help/help.kv')


class HelpView(View,RstDocument):

    def __init__(self, **kwargs):
        super(HelpView, self).__init__(**kwargs)
        with open(os.path.join("modules/help", "help.rst")) as stream:
            self.text = stream.read()


available_views["help"] = HelpView
