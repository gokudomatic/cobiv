from kivy.app import App
from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.factory import Factory

from kivy.vector import Vector

from cobiv.modules.core.gestures.default.pinch_gesture import PinchGesture
from cobiv.modules.core.gestures.gesture_manager import GestureManager


class PinchDetector(Factory.FloatLayout,object):
    __touches = []

    initial_distance = None

    def __init__(self):
        super(PinchDetector, self).__init__()
        self.gesture_manager = GestureManager()
        self.gesture_manager.ready()


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            # self.__touches.append(touch)
            if self.gesture_manager is not None:
                self.gesture_manager.on_touch_down(touch)

                if self.gesture_manager.get_touch_count()>=2:
                    return True

        return super(PinchDetector, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is not self or self.gesture_manager.get_touch_count() == 1:
            return super(PinchDetector, self).on_touch_move(touch)

        if self.gesture_manager is not None:
            self.gesture_manager.on_touch_move(touch)

        # v1 = Vector(self.__touches[0].x, self.__touches[0].y)
        # v2 = Vector(self.__touches[1].x, self.__touches[1].y)
        # actual_dist = (v2 - v1).length()

        # print("distance : {}%".format(actual_dist * 100 / self.initial_distance))

        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            # self.__touches.remove(touch)
            if self.gesture_manager is not None:
                self.gesture_manager.on_touch_up(touch)
                if self.gesture_manager.get_touch_count()>=1:
                    return True

        return super(PinchDetector, self).on_touch_up(touch)

class TestApp(App):

    def lookups(self,category):
        if category=='Gesture':
            return [PinchGesture()]
        else:
            return []

    def build(self):
        return Builder.load_string('''
#:import F kivy.factory.Factory

<Test@Button>:
    size_hint_y: None

PinchDetector:
    ScrollView:
        BoxLayout:
            on_parent: [self.add_widget(F.Test()) for i in range(50)]
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
''')

if __name__ == '__main__':
    TestApp().run()
