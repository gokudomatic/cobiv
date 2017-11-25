from kivy.app import App
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import BooleanProperty, Clock, NumericProperty
from kivy.uix.widget import Widget

from cobiv.modules.core.gestures.default.pinch_gesture import PinchGesture
from cobiv.modules.core.gestures.default.rotate_gesture import RotateGesture
from cobiv.modules.core.gestures.default.swipe_gesture import SwipeGesture
from cobiv.modules.core.gestures.default.unimove_gesture import UnimoveGesture
from cobiv.modules.core.gestures.gesture_manager import GestureManager
from cobiv.modules.hud_components.touchbutton.touchbutton import TouchButton

Builder.load_string('''
#:import F kivy.factory.Factory

<Test@Button>:
    size_hint_y: None

<PinchDetector>:        
    ScrollView:
        BoxLayout:
            on_parent: [self.add_widget(F.Test()) for i in range(50)]
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
    TouchButton:
        id: touch_enabler
        pos_hint: {"x":0.5,"y":1}
''')

class PinchDetector(Factory.FloatLayout,object):
    initial_distance = None
    touch_mode = BooleanProperty(False)

    def __init__(self):
        super(PinchDetector, self).__init__()
        self.gesture_manager = GestureManager()
        self.gesture_manager.ready()

        self.ids.touch_enabler.bind(active=self.on_touch_switch)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            if self.gesture_manager is not None:
                self.gesture_manager.on_touch_down(touch)

                if self.gesture_manager.get_touch_count() >= 2:
                    return True

        if not self.touch_mode or self.ids.touch_enabler.collide_point(touch.x,touch.y):
            return super(PinchDetector, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        # if touch.grab_current is not self or self.gesture_manager.get_touch_count() == 1:
        #     return super(PinchDetector, self).on_touch_move(touch)

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

        return super(PinchDetector, self).on_touch_up(touch)

    def on_touch_switch(self,instance,value):
        self.touch_mode=value

class TestApp(App):
    def lookups(self, category):
        if category == 'Gesture':
            return [PinchGesture(), SwipeGesture(), UnimoveGesture(), RotateGesture()]
        else:
            return []

    def build(self):
        self.root=PinchDetector()
        return self.root


if __name__ == '__main__':
    TestApp().run()
