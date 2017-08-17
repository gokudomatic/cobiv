from kivy.lang import Builder
from kivy.uix.widget import Widget

from cobiv.modules.core.component import Component

Builder.load_string('''
#: import Window kivy.core.window.Window
<SeparatorWidget>:
    canvas:
        Color: 
            rgba: 1,1,1,1
        Rectangle:
            pos: self.pos
            size: self.size
    size_hint_y: None
    height: dp(1)
''')

class SeparatorWidget(Component,Widget):
    pass