from math import floor

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Line
from kivy.uix.widget import Widget

Builder.load_string('''
<ActionMeterWidget>:

<ActionMeter>:
    orientation: 'vertical'
    size_hint: None, None
    Label:
        text: '{} / {}'.format(root.value,root.max_value)
        font_size: '40sp'
    ActionMeterWidget:
        value: root.value / root.max_value

<MainApp>:
    AnchorLayout:
        anchor_x: 'center'
        anchor_y: 'center'
        ActionMeter:
            size: 300, 80
            value: 95
            
''')


class ActionMeter(BoxLayout):
    value = NumericProperty(0)
    max_value = NumericProperty(100)

    class ActionMeterWidget(Widget):

        value=NumericProperty(0)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.bind(pos=self.repaint, size=self.repaint, value=self.repaint)

        def repaint(self, *args):
            self.canvas.clear()
            w = 5
            with self.canvas:
                Color(1, 1, 1, 1)
                Line(points=(self.pos[0], self.pos[1], self.pos[0], self.pos[1] + self.height), width=w, cap='none')
                Line(
                    points=(self.pos[0] + self.width, self.pos[1], self.pos[0] + self.width, self.pos[1] + self.height),
                    width=w, cap='none')

                y = self.pos[1] + self.height / 2
                x = self.pos[0] + w * 2
                for i in range(floor(self.width / (4 * w))):
                    Line(points=(x + i * 4 * w, y, x + (i * 4 + 2) * w, y), width=w, cap='none')

                # cursor
                Color(1, 0, 0, 1)
                x = self.pos[0] + self.value * self.width
                y0 = self.pos[1] + 0.05 * self.height
                y1 = self.pos[1] + 0.95 * self.height
                Line(points=(x, y0, x, y1), width=w // 2, cap='none')


class Main1(App):
    class MainApp(FloatLayout):
        pass

    def build(self):
        return self.MainApp()


if __name__ == '__main__':
    Main1().run()
