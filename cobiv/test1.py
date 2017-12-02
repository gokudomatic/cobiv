from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import StringProperty
from kivy.vector import Vector

Builder.load_string('''
#:import F kivy.factory.Factory
#:import Window kivy.core.window.Window

<PinchDetector>:        
    ScrollView:
        id: scroller
        Image:
            id: image
            source: root.source
            size_hint: None, None
            keep_ratio: True
            size: self.texture.size
''')

class PinchDetector(Factory.FloatLayout,object):

    source = StringProperty('1.jpg')

    def __init__(self):
        super(PinchDetector, self).__init__()


    def on_touch_down(self, touch):
        print Vector(self.ids.scroller.convert_distance_to_scroll(*self.ids.image.to_widget(Window.width/2,Window.height/2)))
        x,y=self.ids.image.to_widget(touch.x,touch.y)
        print touch.pos,(x,y),self.ids.scroller.convert_distance_to_scroll(x,y),(self.ids.scroller.scroll_x,self.ids.scroller.scroll_y)

        return super(PinchDetector, self).on_touch_down(touch)
    #
    # def on_touch_move(self, touch):
    #
    #     return True
    #
    # def on_touch_up(self, touch):
    #     if touch.grab_current is self:
    #         touch.ungrab(self)
    #         if self.gesture_manager is not None:
    #             self.gesture_manager.on_touch_up(touch)
    #             if self.gesture_manager.get_touch_count() >= 1:
    #                 return True
    #
    #     return super(PinchDetector, self).on_touch_up(touch)


class TestApp(App):

    def build(self):
        self.root=PinchDetector()
        return self.root


if __name__ == '__main__':
    TestApp().run()
