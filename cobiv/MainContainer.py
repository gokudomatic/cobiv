import shlex, logging

import sys
from kivy.app import App
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.clock import Clock, mainthread

this = sys.modules[__name__]


class MainContainer(FloatLayout):
    logger = logging.getLogger(__name__)
    session = None
    cmd_input = ObjectProperty(None)
    current_view = ObjectProperty(None)
    hud_layout = ObjectProperty(None)
    modal_hud_layout = ObjectProperty(None)
    notification_hud_layout = ObjectProperty(None)

    aliases = {}

    cmd_visible = True

    is_enter_command = False

    available_views = {}

    def __init__(self, **kwargs):
        super(MainContainer, self).__init__(**kwargs)

        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._set_cmd_visible(False)

    def ready(self):
        self.session = App.get_running_app().lookup("session", "Entity")
        print("session found : {}".format(self.session))
        self.gesture_manager = App.get_running_app().lookup("gesture_manager", "Entity")
        self.ids.touch_switcher.ready()

        self.session.set_action("q", self.quit)
        self.session.set_action("fullscreen", self.toggle_fullscreen)
        self.session.set_action("switch-view", self.switch_view)
        self.session.set_action("hello", self.hello)
        self.session.set_action("memory", self.memory)
        self.session.set_action("set-command", self.set_command)
        self.session.set_action("back", self.go_history_back)

        view_context = self.session.get_context("view")
        view_context.fn = self.switch_view

    def memory(self):
        import os
        import psutil
        process = psutil.Process(os.getpid())
        self.logger.debug(str(process.memory_info().rss / float(2 ** 20)) + " MB")

    def switch_view(self, view_name):
        if len(self.current_view.children) > 0:
            self.current_view.children[0].on_switch_lose_focus()
            self.session.push_context("view")

        session = App.get_running_app().lookup("session", "Entity")

        self.current_view.clear_widgets()
        if view_name in self.available_views.keys():
            view = self.available_views[view_name]
            self.current_view.add_widget(view)
            view.on_switch()
            session.get_context("view").args['view_name'] = view_name

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
        if keycode[0] == 27 and self.cmd_visible:
            self._set_cmd_visible(False)
        elif not self.cmd_visible:
            if keycode[0] == 46 and modcode == 1:
                self._toggle_cmd(":")
            elif keycode[0] == 304:
                pass
            elif keycode[0] in self.session.cmd_hotkeys and not self.is_enter_command:
                if keycode[0] == 13:
                    self.logger.info("enter pressed")
                view_name = self.get_view_name()
                command = self.session.get_hotkey_command(keycode[0], modcode, view_name)
                if command:
                    self.execute_cmds(command)
                else:
                    command = self.session.get_hotkey_command(keycode[0], modcode)
                    if command:
                        self.execute_cmds(command)
            else:
                if keycode[0] != 13:
                    self.logger.info("code : " + str(keycode) + " " + str(modifiers))
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
            self.execute_cmds(text[1:])

    def execute_cmds(self, command, force_default=False, recursive_iteration=0):

        lines = command.split('|')
        for line in lines:
            self.execute_cmd(line.strip(), recursive_iteration=recursive_iteration + 1, force_default=force_default)

    def execute_cmd(self, command, recursive_iteration, force_default=False):
        if recursive_iteration > 100:
            return

        line = shlex.split(command)
        action = line[0]
        args = line[1:]

        found_cmd = action in self.session.cmd_actions
        if not found_cmd and action in self.aliases:
            alias_action = action
            alias_command = self.aliases[alias_action]

            new_command = alias_command + command[len(action):]
            self.execute_cmds(new_command, recursive_iteration=recursive_iteration + 1, force_default=force_default)

        elif found_cmd:
            list_func = self.session.cmd_actions[action]
            profile_name = "default"
            if not force_default and self.get_view_name() in list_func:
                profile_name = self.get_view_name()
            if profile_name in list_func:
                func = list_func[profile_name]
                try:
                    func(*args)
                except TypeError as err:
                    self.logger.error(
                        "The number of arguments for action " + action + " (" + profile_name + ") is not right : " + str(
                            err))

    def quit(self, *args):
        if len(self.current_view.children) > 0:
            self.current_view.children[0].on_switch_lose_focus()
        App.get_running_app().stop()

    def toggle_fullscreen(self, *args):
        Window.toggle_fullscreen()

    def hello(self, *args):
        self.notify("Hi " + (args[0] if len(args) > 0 else "there") + "!", is_error=False)

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
        self.notification_hud_layout.notify(text=message, error=is_error)

    @mainthread
    def show_status(self, key=None, renderer=None, **kwargs):
        if renderer is None:
            render_class = Factory.NotificationLabel
        else:
            render_class = Factory.get(renderer)
        self.notification_hud_layout.notify(key, render_class, **kwargs)

    def read_yaml_main_config(self, config):
        session = App.get_running_app().lookup("session", "Entity")
        if 'main' in config:
            for hotkey_config in config['main'].get('hotkeys', []):
                session.set_hotkey(int(hotkey_config['key']), hotkey_config['binding'],
                                   hotkey_config.get('modifiers', 0))

        if 'aliases' in config:
            aliases = config['aliases']
            for alias in aliases:
                self.aliases[alias] = aliases[alias]

    def build_yaml_main_config(self):
        return {
            'main': {
                'hotkeys': [
                    {'key': '113', 'binding': 'q'},
                    {'key': '167', 'binding': 'set-command search'},
                    {'key': '292', 'binding': 'fullscreen'}
                ]
            }
        }

    def set_command(self, *args):
        self._toggle_cmd(":" + " ".join(args) + " ")

    # Gesture methods
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            if self.gesture_manager is not None:
                self.gesture_manager.on_touch_down(touch)

                if self.gesture_manager.get_touch_count() >= 2:
                    return True

        touch_switcher = self.ids.touch_switcher
        if not touch_switcher.active or touch_switcher.collide_point(*touch.pos):
            return super(MainContainer, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is not self or self.gesture_manager.get_touch_count() == 1:
            return super(MainContainer, self).on_touch_move(touch)

        if self.gesture_manager is not None:
            self.gesture_manager.on_touch_move(touch)

        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.gesture_manager is not None:
                self.gesture_manager.on_touch_up(touch)
                if self.gesture_manager.get_touch_count() >= 1:
                    return True

        return super(MainContainer, self).on_touch_up(touch)

    def go_history_back(self):
        view_context = self.session.pop_context()
        if view_context is not None:
            self.session.skip_push_context=True
            fn = view_context.fn
            args = view_context.args
            if fn is not None:
                fn(**args)
            self.session.skip_push_context=False
