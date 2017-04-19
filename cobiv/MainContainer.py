import os
import shlex

import sys
from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.clock import Clock, mainthread

from cobiv.common import *
from cobiv.hud import HUD
from os.path import expanduser

this = sys.modules[__name__]


class MainContainer(FloatLayout):
    cmd_input = ObjectProperty(None)
    current_view = ObjectProperty(None)
    hud_layout = ObjectProperty(None)
    modal_hud_layout = ObjectProperty(None)
    notification_hud_layout = ObjectProperty(None)

    cmd_visible = True

    is_enter_command = False

    available_views = {}

    def __init__(self, **kwargs):
        super(MainContainer, self).__init__(**kwargs)

        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._set_cmd_visible(False)

        set_action("q", self.quit)
        set_action("fullscreen", self.toggle_fullscreen)
        set_action("switch-view", self.switch_view)
        set_action("hello", self.hello)
        set_action("memory", self.memory)

    def ready(self):
        # self.execute_cmd("search")
        pass

    def memory(self):
        import os
        import psutil
        process = psutil.Process(os.getpid())
        print(str(process.memory_info().rss / float(2 ** 20)) + " MB")

    def switch_view(self, view_name):
        # print "switch to "+view_name
        if len(self.current_view.children) > 0:
            self.current_view.children[0].on_switch_lose_focus()

        self.current_view.clear_widgets()
        if view_name in self.available_views.keys():
            view = self.available_views[view_name]
            self.current_view.add_widget(view)
            view.on_switch()

    def get_view(self):
        return self.current_view.children[0] if len(self.current_view.children) > 0 else None

    def get_view_name(self):
        if len(self.current_view.children) > 0:
            return self.current_view.children[0].get_name()
        else:
            return None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):

        modcode = self.get_modifiers_code(modifiers)

        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard

        # if escape, close term
        if keycode[0] == 27L and self.cmd_visible:
            self._set_cmd_visible(False)
        elif not self.cmd_visible:
            if keycode[0] == 46L and modcode == 1:
                self._toggle_cmd(":")
            elif keycode[0] == 267:
                self._set_cmd_visible(True, "/")
            elif cmd_hotkeys.has_key(keycode[0]) and not self.is_enter_command:
                if keycode[0] == 13L:
                    print "enter pressed"
                view_name = self.get_view_name()
                command = get_hotkey_command(keycode[0], modcode, view_name)
                if command:
                    self.execute_cmd(command)
                else:
                    command = get_hotkey_command(keycode[0], modcode)
                    if command:
                        self.execute_cmd(command)
            else:
                print "code : " + str(keycode) + " " + str(modifiers)
                pass

            self.is_enter_command = False

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
        self.is_enter_command = True
        if text[0] == ":":
            self.execute_cmd(text[1:])

    def execute_cmd(self, command):
        line = shlex.split(command)
        action = line[0]
        args = line[1:]
        if cmd_actions.has_key(action):
            list_func = cmd_actions[action]
            profile_name = "default"
            if list_func.has_key(self.get_view_name()):
                profile_name = self.get_view_name()
            if list_func.has_key(profile_name):
                func = list_func[profile_name]
                func(*args)

    def quit(self, *args):
        if len(self.current_view.children) > 0:
            self.current_view.children[0].on_switch_lose_focus()
        App.get_running_app().stop()

    def toggle_fullscreen(self, *args):
        Window.toggle_fullscreen()

    def hello(self, *args):
        self.notify("Hi " + (args[0] if len(args) > 0 else "there") + "!", is_error=True)

    @mainthread
    def show_progressbar(self):
        self.modal_hud_layout.visible = True
        progressbar = App.get_running_app().lookup('progresshud', 'Hud')
        if not progressbar in self.modal_hud_layout.children:
            self.modal_hud_layout.add_widget(progressbar)

    @mainthread
    def close_progressbar(self):
        self.modal_hud_layout.visible = False
        progressbar = App.get_running_app().lookup('progresshud', 'Hud')
        self.modal_hud_layout.remove_widget(progressbar)

    @mainthread
    def set_progressbar_value(self, value, caption=None):
        progressbar = App.get_running_app().lookup('progresshud', 'Hud')
        progressbar.value = value
        if caption != None:
            progressbar.caption = caption

    @mainthread
    def set_progressbar_caption(self, caption):
        App.get_running_app().lookup('progresshud', 'Hud').caption = caption

    @mainthread
    def notify(self, message, is_error=False):
        self.notification_hud_layout.notify(message, error=is_error)

    def read_yaml_main_config(self, config):
        if config.has_key('main'):
            for hotkey_config in config['main'].get('hotkeys', []):
                set_hotkey(long(hotkey_config['key']), hotkey_config['binding'], hotkey_config.get('modifiers', 0))

    def build_yaml_main_config(self):
        return {
            'main': {
                'hotkeys': [
                    {'key': '113', 'binding': 'q'},
                    {'key': '292', 'binding': 'fullscreen'}
                ]
            },
            'thumbnails': {
                'path': os.path.join(expanduser('~'), '.cobiv', 'thumbnails')
            }
        }
