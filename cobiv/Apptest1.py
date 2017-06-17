import kivy
from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.core.window import Window
Window.size = (360, 360)

kivy.require('1.9.1')


class W1(FloatLayout):
    def __init__(self, **kwargs):
        super(W1, self).__init__(**kwargs)
        from kivy.clock import Clock
        Clock.schedule_once(self.msg)

    def msg(self,dt):
        print self.height

class Test1(App):

    def build(self):
        self.root = W1(size_hint=(1,1))

        return self.root

if __name__ == '__main__':
    Test1().run()
