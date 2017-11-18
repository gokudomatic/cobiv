from kivy.core.window import Window
from kivy.vector import Vector

from cobiv.modules.core.gestures.gesture import Gesture


class UnimoveGesture(Gesture):
    initial_touches = None
    not_moving_uid=None

    def finalize(self, touches, strokes):
        moving_uid=[t.uid for t in touches if t.uid!=self.not_moving_uid][0]
        moving_strokes=strokes[moving_uid]
        anchor=self.initial_touches[self.not_moving_uid]

        v=moving_strokes[0]
        w,h=Window.size
        print("unimove",(int(anchor.x/float(w)*3),int(anchor.y/float(h)*3)),v)


    def process(self, touches, strokes):
        pass

    def required_touch_count(self):
        return 2

    def validate(self, touches, strokes):

        uid0=strokes.keys()[0]
        uid1=strokes.keys()[1]

        stroke0=strokes[uid0][-1]
        stroke1=strokes[uid1][-1]

        l0=stroke0.length()
        l1=stroke1.length()

        if l0+l1==1 and l0*l1==0:
            self.not_moving_uid=uid0 if l0==0 else uid1
            print("unimove")
            return True
        return False

    def initialize(self, touches):
        self.initial_touches = {}
        for t in touches:
            self.initial_touches[t.uid]=Vector(t.x,t.y)