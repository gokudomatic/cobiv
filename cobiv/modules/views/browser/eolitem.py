from kivy.lang import Builder
from kivy.properties import NumericProperty, BooleanProperty, ObjectProperty
from kivy.uix.label import Label

Builder.load_string('''
<EOLItem>:
    text: 'EOL'
    color: 0,0,1,1
    size_hint: None, None
    size: root.cell_size, root.cell_size
    canvas.before:
        Color:
            rgba: 0,0,1,1
        Line:
            width: 2
            rounded_rectangle: self.x+10,self.y+10,self.width-20,self.height-20,10
        Color:
            rgba: 1,0,0,1 if self.selected else 0
        Line:
            width: 2
            rectangle: self.x+2,self.y+2,self.width-4,self.height-4
''')


class EOLItem(Label):
    cell_size = NumericProperty(None)
    selected = BooleanProperty(None)
    container = ObjectProperty(None)

    file_id = None
    position = None

    def __init__(self, **kwargs):
        super(EOLItem, self).__init__(**kwargs)

    def set_selected(self, value):
        self.selected = value

    def is_selected(self):
        return self.selected

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.container.select_EOL()
            return True

    def set_marked(self, value):
        pass

    def is_marked(self):
        return False
