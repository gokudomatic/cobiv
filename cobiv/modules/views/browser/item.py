from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget


class SimpleItem(BoxLayout):
    thumb = ObjectProperty(None, allownone=True)
    cell_size = NumericProperty(None)
    file_id = NumericProperty(None)
    position = NumericProperty(None)
    container = ObjectProperty(None)
    duration = NumericProperty(None)

    def __init__(self, **kwargs):
        super(SimpleItem, self).__init__(**kwargs)

        self.add_widget(self.thumb)

        self.size_hint = (None, None)
        self.bind(cell_size=self.on_cell_size)

    def on_cell_size(self, instance, value):
        self.size = (value, value)

    def set_selected(self, value):
        self.thumb.selected = value

    def is_selected(self):
        return self.thumb.selected if self.thumb is not None else False

    def set_marked(self, value):
        if value is None:
            self.thumb.marked = not self.thumb.marked
        else:
            self.thumb.marked = value

    def is_marked(self):
        return self.thumb.marked
