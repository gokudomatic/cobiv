from kivy.vector import Vector

from cobiv.modules.core.gestures.gesture import Gesture


class SwipeGesture(Gesture):
    initial_distance = None
    initial_touches = None

    def finalize(self, touch, strokes):
        self.get_app().fire_event("on_stop_gesture_swipe")

    def process(self, touches, strokes):
        uid = touches[0].uid
        v = Vector(touches[0].x, touches[0].y) - self.initial_touches[uid]
        a = v.angle((1, 0))
        self.get_app().fire_event("on_gesture_swipe", v, self.initial_touches[uid])

    def required_touch_count(self):
        return 2

    def validate(self, touches, strokes):

        v_orig = Vector(0, 0)
        for i in self.initial_touches:
            v_orig = self.initial_touches[i] - v_orig
        if v_orig.length() > 100:
            return False

        v_sum = Vector(0, 0)
        for t in touches:
            v_old = self.initial_touches[t.uid]
            v_new = Vector(t.x, t.y)

            v_norm = (v_new - v_old).normalize()
            if v_norm.length() == 0:
                return False

            v_sum = v_norm - v_sum

        return v_sum.length() < 1

    def initialize(self, touches):
        self.initial_touches = {}
        for t in touches:
            self.initial_touches[t.uid] = Vector(t.x, t.y)
