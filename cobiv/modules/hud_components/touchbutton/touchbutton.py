from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, Clock
from kivy.uix.widget import Widget

Builder.load_string('''
<TouchButton>:
    rad: self.rad_large if self.active else self.rad_small
    canvas:
        Color:
            rgba: 1,0,0,0.8 if self.active else 0.4
        Ellipse:
            pos: self.x-self.width/2,self.y-self.height/2
            size: self.size
    size_hint: None, None
    size: self.rad, self.rad
''')

class TouchButton(Widget):

    rad_small = NumericProperty(50)
    rad_large = NumericProperty(150)
    rad = NumericProperty(None)
    active=BooleanProperty(False)

    def __init__(self, **kwargs):
        super(TouchButton, self).__init__(**kwargs)
        self.trigger=Clock.create_trigger(self.on_toggle,0.1)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.trigger()
            return True
        else:
            return super(TouchButton,self).on_touch_down(touch)

    def on_toggle(self,dt):
        self.active=not self.active

    def collide_point(self, x, y):
        return (x-self.x)**2 + (y-self.y)**2 <= self.rad**2
