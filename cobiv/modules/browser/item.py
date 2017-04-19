import math

from kivy.atlas import CoreImage
from kivy.lang import Builder
from kivy.properties import ObjectProperty, Clock, NumericProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage

from cobiv.libs.magnet import Magnet

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


class Item(Magnet):
    thumb = ObjectProperty(None, allownone=True)
    container = ObjectProperty(None)
    cell_size = NumericProperty(None)
    file_id = NumericProperty(None)
    position = NumericProperty(None)

    def __init__(self, **kwargs):
        super(Item, self).__init__(**kwargs)

        self.add_widget(self.thumb)

        self.size_hint = (None, None)
        self.bind(cell_size=self.on_cell_size)

    def on_cell_size(self, instance, value):
        self.size = (value, value)

    def on_img(self, *args):
        self.clear_widgets()

        if self.thumb:
            Clock.schedule_once(lambda *x: self.add_widget(self.thumb), 0)

    def on_touch_down(self, touch, *args):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.remove_widget(self.thumb)
            self.container.add_widget(self.thumb)

            abs_pos = self.container.ids.scroll_view.to_parent(touch.pos[0], touch.pos[1])

            self.thumb.center = abs_pos

            return True

        return super(Item, self).on_touch_down(touch, *args)

    def on_touch_move(self, touch, *args):
        grid_layout = self.container.ids.grid_layout

        if touch.grab_current == self:
            abs_pos = self.container.ids.scroll_view.to_parent(touch.pos[0], touch.pos[1])

            self.thumb.center = abs_pos

            grid_layout.remove_widget(self)

            cnt_max = len(grid_layout.children)
            idx = min(grid_layout.cols * math.floor((grid_layout.height - touch.pos[1]) / self.cell_size) + math.floor(
                touch.pos[0] / self.cell_size), cnt_max)

            i = int(cnt_max - idx)

            if i > 0:
                grid_layout.add_widget(self, i)
            else:
                grid_layout.add_widget(self)

        return super(Item, self).on_touch_move(touch, *args)

    def on_touch_up(self, touch, *args):
        if touch.grab_current == self:
            self.thumb.center = touch.pos
            self.container.remove_widget(self.thumb)
            self.add_widget(self.thumb)
            touch.ungrab(self)
            self.container.on_image_touch_up(self)
            return True

        return super(Item, self).on_touch_up(touch, *args)

    def set_selected(self,value):
        self.thumb.selected=value