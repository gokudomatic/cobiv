from kivy.vector import Vector

from cobiv.modules.core.gestures.gesture import Gesture


class PinchGesture(Gesture):
    initial_distance = None
    center = None
    initial_touches = None

    def finalize(self, touch, strokes):
        pass

    def process(self, touches, strokes):
        v = Vector(touches[1].x, touches[1].y) - Vector(touches[0].x, touches[0].y)
        ratio = v.length() / self.initial_distance
        self.get_app().fire_event("on_gesture_pinch",ratio,self.center)

    def required_touch_count(self):
        return 2

    def validate(self, touches, strokes):

        v_sum = Vector(0, 0)
        sum_dot_base = 0

        for t in touches:
            v_old = Vector(self.initial_touches[t.uid][0], self.initial_touches[t.uid][1])
            v_new = Vector(t.x, t.y)

            v_norm = (v_new - v_old).normalize()
            if v_norm.length() == 0:
                return False

            v_base = (v_old - self.center).normalize()
            print(v_old,v_new, v_norm, v_base,v_base.dot(v_norm))
            sum_dot_base += v_base.dot(v_norm)
            v_sum += v_norm


        return abs(sum_dot_base) >= 1.85 and v_sum.length() < 1

    def initialize(self, touches):
        v = [Vector(t.x, t.y) for t in touches]

        v_diff = v[1] - v[0]
        self.center = v[0] + v_diff / 2
        self.initial_distance = float(v_diff.length())
        self.initial_touches = {touches[0].uid:(touches[0].x,touches[0].y),touches[1].uid:(touches[1].x,touches[1].y)}