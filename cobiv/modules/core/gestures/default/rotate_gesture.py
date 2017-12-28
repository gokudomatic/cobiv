from kivy.vector import Vector

from cobiv.modules.core.gestures.gesture import Gesture


class RotateGesture(Gesture):
    initial_distance = None
    center = None
    initial_vector = None

    def finalize(self, touch, strokes):
        pass

    def process(self, touches, strokes):
        v = Vector(touches[1].x, touches[1].y) - Vector(touches[0].x, touches[0].y)
        angle = self.initial_vector.angle(v)
        uid = touches[0].uid
        self.get_app().fire_event("on_gesture_rotate", angle, self.initial_touches[uid])

    def required_touch_count(self):
        return 2

    def validate(self, touches, strokes):
        if len(touches) != 2:
            return False

        v = [Vector(t.x, t.y) for t in touches]
        v_diff = v[1] - v[0]
        new_center = v[0] + v_diff / 2

        return abs(v_diff.length() - self.initial_distance) < 20 and (new_center.distance(self.center) < 20)

    def initialize(self, touches):
        v = [Vector(t.x, t.y) for t in touches]

        v_diff = v[1] - v[0]
        self.center = v[0] + v_diff / 2
        self.initial_vector = v_diff
        self.initial_distance = v_diff.length()
