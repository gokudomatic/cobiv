from kivy.vector import Vector

from cobiv.modules.core.gestures.gesture import Gesture


class PinchGesture(Gesture):

    initial_distance = None
    center=None

    def finalize(self, touch, strokes):
        pass

    def process(self, touches, strokes):
        # print "process"
        v=Vector(touches[1].x,touches[1].y)-Vector(touches[0].x,touches[0].y)
        ratio=v.length()/self.initial_distance
        # print("{}% {}".format(ratio*100,self.center))
        #TODO send signal with ratio

    def required_touch_count(self):
        return 2

    def validate(self, strokes):
        path1,path2=strokes.values()[0:2]

        last_vector1=path1[-1]
        last_vector2=path2[-1]

        # print(last_vector1,last_vector2)

        last_distance=(last_vector1+last_vector2).length()
        last_length1=last_vector1.length()
        last_length2=last_vector2.length()

        result=(last_distance==0 and last_length1>0) or (last_length1*last_length2==0 and last_length1+last_length2>0)
        if result:

            print(last_vector1,last_vector2)
        return result

    def initialize(self, touches):
        print "init"
        v1=Vector(touches[1].x,touches[1].y)
        v0=Vector(touches[0].x,touches[0].y)

        v=v1-v0
        self.center=v0+v/2
        self.initial_distance=float(v.length())
