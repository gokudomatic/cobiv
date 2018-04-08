from kivy.lang import Builder
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout

Builder.load_string('''
<Thumb>:
    orientation: 'vertical'
    size_hint: None, None
    size: root.cell_size, root.cell_size
    padding: 5
    canvas:
        Color:
            rgba: 0.25,0.8,1,0.7 if root.marked else 0
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 1,0,0,1 if root.selected else 0
        Line:
            width: 2
            rectangle: self.pos[0]+2,self.pos[1]+2,self.size[0]-4,self.size[1]-4
    Label:
        text:root.caption
        size_hint: 1, None
        height: self.texture_size[1]
''')


class Thumb(BoxLayout):
    cell_size = NumericProperty(None)
    caption = StringProperty(None)

    selected = BooleanProperty(None)
    marked = BooleanProperty(None)
    image = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Thumb, self).__init__(**kwargs)
        self.add_widget(self.image, 1)
