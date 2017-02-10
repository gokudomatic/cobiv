import shlex

from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.clock import Clock

from cobiv.viewlist import available_views, cmd_actions, cmd_hotkeys
import cobiv.modules.help.helpview


class MainContainer(FloatLayout):
    cmd_input = ObjectProperty(None)
    current_view = ObjectProperty(None)

    cmd_visible = True

    def __init__(self, **kwargs):
        super(MainContainer, self).__init__(**kwargs)

        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._set_cmd_visible(False)

        cmd_actions["q"] = {"default": self.quit}
        cmd_actions["fullscreen"] = {"default": self.toggle_fullscreen}
        cmd_hotkeys[292] = {"default": {0: "fullscreen"}}
        cmd_hotkeys[113L] = {"default": {0: "q"}}

        # test
        ViewClass = available_views["help"]
        self.current_view.clear_widgets()
        self.current_view.add_widget(ViewClass())

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
                hotkeys_profiles = cmd_hotkeys[keycode[0]]
                if hotkeys_profiles.has_key("default"):
                    hotkeys=hotkeys_profiles["default"]
                    if hotkeys.has_key(modcode):
                        self.execute_cmd(hotkeys[modcode])
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
        print args
        if cmd_actions.has_key(action):
            list_func = cmd_actions[action]
            func = list_func["default"]
            func(*args)

    def quit(self, *args):
        App.get_running_app().stop()

    def toggle_fullscreen(self, *args):
        Window.toggle_fullscreen()
