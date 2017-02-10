from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.textinput import TextInput


class ConsoleInput(TextInput):
    pass


class MainContainer(FloatLayout):

    cmd_input = ObjectProperty(None)
    current_view = ObjectProperty(None)

    cmd_visible = True

    def __init__(self, **kwargs):
        super(MainContainer, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)


    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        if keycode[0] == 27L and self.cmd_visible:
            self._set_cmd_visible(False)

        if keycode[0] == 46L and 'shift' in modifiers and not self.cmd_visible:
            self._toggle_cmd(":")

        if keycode[0] == 267 and not self.cmd_visible:
            self._set_cmd_visible(True,"/")

        return True

    def _toggle_cmd(self,prefix=""):
        self._set_cmd_visible(not self.cmd_visible,prefix)

    def _set_cmd_visible(self,value,prefix=""):
        self.cmd_visible = value
        if value:
            print "set visible"
            self.cmd_input.opacity=1
            self.cmd_input.disable=False
            self.cmd_input.text=prefix
            Clock.schedule_once(self.set_cmd_focus)
        else:
            print "hide"
            self.cmd_input.opacity=0
            self.cmd_input.disable=True
            self.current_view.focus=True
            self.cmd_input.text = ""

    def set_cmd_focus(self,dt):
        self.cmd_input.focus = True

    def on_cmd_focus(self,instance, value):
        if value:
            print('User focused', instance)
        else:
            print('User defocused', instance)
            self._set_cmd_visible(False)