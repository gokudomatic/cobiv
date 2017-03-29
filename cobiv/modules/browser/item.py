import math
from kivy.properties import ObjectProperty, Clock, NumericProperty

from cobiv.libs.magnet import Magnet


class Item(Magnet):
    img = ObjectProperty(None, allownone=True)
    container = ObjectProperty(None)
    cell_size = NumericProperty(None)
    id = NumericProperty(None)
    position = NumericProperty(None)

    def __init__(self, **kwargs):
        super(Item, self).__init__(**kwargs)
        self.size_hint=(None, None)
        self.bind(cell_size=self.on_cell_size)

    def on_cell_size(self,instance,value):
        self.size=(value,value)

    def on_img(self, *args):
        self.clear_widgets()

        if self.img:
            Clock.schedule_once(lambda *x: self.add_widget(self.img), 0)

    def on_touch_down(self, touch, *args):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.remove_widget(self.img)
            self.container.add_widget(self.img)

            abs_pos = self.container.ids.scroll_view.to_parent(touch.pos[0], touch.pos[1])

            self.img.center = abs_pos

            return True

        return super(Item, self).on_touch_down(touch, *args)

    def on_touch_move(self, touch, *args):
        grid_layout = self.container.ids.grid_layout

        if touch.grab_current == self:
            abs_pos = self.container.ids.scroll_view.to_parent(touch.pos[0], touch.pos[1])

            self.img.center = abs_pos

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
            self.img.center = touch.pos
            self.container.remove_widget(self.img)
            self.add_widget(self.img)
            touch.ungrab(self)
            self.container.on_image_touch_up(self)
            return True

        return super(Item, self).on_touch_up(touch, *args)
