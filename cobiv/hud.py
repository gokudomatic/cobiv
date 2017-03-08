from kivy.animation import Animation
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout

Builder.load_string('''

<NotificationLabel>:
    size_hint: None, None
    size: self.texture_size

<HUD>:
    size_hint: None, None
    size: win.Window.size
''')

class HUD(RelativeLayout):
    visible = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(HUD, self).__init__(**kwargs)

        self.bind(visible=self.on_visible)
        self.bind(height=self.on_visible)

    def on_visible(self,instance,value):
        self.pos=(0,0 if self.visible else self.height)

class NotificationLabel(Label):
    pass

class NotificationHUD(HUD):
    def __init__(self, **kwargs):
        super(NotificationHUD, self).__init__(**kwargs)
        self.visible=True

    def notify(self,message,error=False):
        msg=NotificationLabel(text=message,pos=(5,1),color=(1,0,0,1) if error else (1,1,1,1))
        msg_shadow=NotificationLabel(text=message,pos=(6,0),color=(0,0,0,1))
        anim=Animation(y=200,color=(1,0,0,0) if error else (1,1,1,0),duration=2.)
        anim.bind(on_complete=lambda instance,value: self.remove_widget(msg))

        anim_shadow=Animation(y=199,color=(0,0,0,0),duration=2.)
        anim_shadow.bind(on_complete=lambda instance,value: self.remove_widget(msg_shadow))

        self.add_widget(msg_shadow)
        self.add_widget(msg)
        anim.start(msg)
        anim_shadow.start(msg_shadow)