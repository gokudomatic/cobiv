import shlex

import sys
from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.clock import Clock

from cobiv.common import *
import cobiv.modules.help.helpview
import cobiv.modules.viewer.Viewer
from cobiv.modules.imageset.ImageSet import current_imageset
import cobiv.modules.grapheekdb.db

this = sys.modules[__name__]

class MainContainer(FloatLayout):
    cmd_input = ObjectProperty(None)
    current_view = ObjectProperty(None)

    cmd_visible = True

    def __init__(self, **kwargs):
        super(MainContainer, self).__init__(**kwargs)

        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._set_cmd_visible(False)

        set_action("q",self.quit)
        set_action("fullscreen",self.toggle_fullscreen)
        set_hotkey(292,"fullscreen")
        set_hotkey(113L,"q")

        # test
        # self.switch_view("help")

        self.switch_view("viewer")


    def switch_view(self,view_name):
        clazz = available_views[view_name]
        self.current_view.clear_widgets()
        self.current_view.add_widget(clazz())


    def get_view_name(self):
        return self.current_view.children[0].get_name()

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):

        modcode = self.get_modifiers_code(modifiers)

        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        if keycode[0] == 27L and self.cmd_visible:
            self._set_cmd_visible(False)
        elif not self.cmd_visible:
            if keycode[0] == 46L and modcode == 1:
                self._toggle_cmd(":")
            elif keycode[0] == 267:
                self._set_cmd_visible(True, "/")
            elif cmd_hotkeys.has_key(keycode[0]):
                command=get_hotkey_command(keycode[0],modcode)
                if command:
                    self.execute_cmd(command)
                else:
                    view_name=self.get_view_name()
                    command=get_hotkey_command(keycode[0],modcode,view_name)
                    if command:
                        self.execute_cmd(command)
            else:
                print "code : " + str(keycode) + " " + str(modifiers)

        return True

    def get_modifiers_code(self, modifiers):
        modcode = 0
        for m in modifiers:
            if m == "shift":
                modcode += 1
            elif m == "alt":
                modcode += 2
            elif m == "ctrl":
                modcode += 4
            elif m == "meta":
                modcode += 8

        return modcode

    def _toggle_cmd(self, prefix=""):
        self._set_cmd_visible(not self.cmd_visible, prefix)

    def _set_cmd_visible(self, value, prefix=""):
        self.cmd_visible = value
        if value:
            self.cmd_input.opacity = 1
            self.cmd_input.disable = False
            self.cmd_input.text = prefix
            Clock.schedule_once(self.set_cmd_focus)
        else:
            self.cmd_input.opacity = 0
            self.cmd_input.disable = True
            self.current_view.focus = True
            self.cmd_input.text = ""

    def set_cmd_focus(self, dt):
        self.cmd_input.focus = True

    def on_cmd_focus(self, instance, value):
        if not value:
            self._set_cmd_visible(False)

    def on_enter_cmd(self, text):
        if text[0] == ":":
            self.execute_cmd(text[1:])

    def execute_cmd(self, command):
        line = shlex.split(command)
        action = line[0]
        args = line[1:]
        if cmd_actions.has_key(action):
            list_func = cmd_actions[action]
            profile_name="default"
            if list_func.has_key(self.get_view_name()):
                profile_name=self.get_view_name()
            if list_func.has_key(profile_name):
                func = list_func[profile_name]
                func(*args)

    def quit(self, *args):
        App.get_running_app().stop()

    def toggle_fullscreen(self, *args):
        Window.toggle_fullscreen()