from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.clock import Clock

cmd_actions={}

class MainContainer(FloatLayout):

    cmd_input = ObjectProperty(None)
    current_view = ObjectProperty(None)

    cmd_visible = True

    def __init__(self, **kwargs):
        super(MainContainer, self).__init__(**kwargs)

        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._set_cmd_visible(False)

        cmd_actions["q"]=self.quit
        cmd_actions["fullscreen"]=self.toggle_fullscreen

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        if keycode[0] == 27L and self.cmd_visible:
            self._set_cmd_visible(False)
        elif keycode[0] == 46L and 'shift' in modifiers and not self.cmd_visible:
            self._toggle_cmd(":")

        elif keycode[0] == 267 and not self.cmd_visible:
            self._set_cmd_visible(True,"/")
        elif keycode[0] == 292:
            self.toggle_fullscreen()
        elif keycode[0] == 113L:
            self.quit()
        else:
            print "code : "+str(keycode)+" ["+str(modifiers)+"]"

        return True

    def _toggle_cmd(self,prefix=""):
        self._set_cmd_visible(not self.cmd_visible,prefix)

    def _set_cmd_visible(self,value,prefix=""):
        self.cmd_visible = value
        if value:
            self.cmd_input.opacity=1
            self.cmd_input.disable=False
            self.cmd_input.text=prefix
            Clock.schedule_once(self.set_cmd_focus)
        else:
            self.cmd_input.opacity=0
            self.cmd_input.disable=True
            self.current_view.focus=True
            self.cmd_input.text = ""

    def set_cmd_focus(self,dt):
        self.cmd_input.focus = True

    def on_cmd_focus(self,instance, value):
        if not value:
            self._set_cmd_visible(False)

    def on_enter_cmd(self,text):
        if text[0]==":":
            command=text[1:]
            if cmd_actions.has_key(command):
                func=cmd_actions[command]
                func()

    def quit(self):
        App.get_running_app().stop()

    def toggle_fullscreen(self):
        Window.toggle_fullscreen()