import math

from kivy.properties import ObjectProperty, Clock, NumericProperty

from cobiv.libs.magnet import Magnet
from cobiv.modules.views.browser.eolitem import EOLItem

class DraggableItem(Magnet):
    thumb = ObjectProperty(None, allownone=True)
    container = ObjectProperty(None)
    cell_size = NumericProperty(None)
    file_id = NumericProperty(None)
    position = NumericProperty(None)
    temp_idx = None

    def __init__(self, **kwargs):
        super(DraggableItem, self).__init__(**kwargs)

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

        return super(DraggableItem, self).on_touch_down(touch, *args)

    def on_touch_move(self, touch, *args):
        grid_layout = self.container.ids.grid_layout

        if touch.grab_current == self:
            abs_pos = self.container.ids.scroll_view.to_parent(touch.pos[0], touch.pos[1])

            self.thumb.center = abs_pos

            grid_layout.remove_widget(self)

            cnt_max = len(grid_layout.children)
            x = math.floor(touch.pos[0] / self.cell_size)
            y = math.floor((grid_layout.height + self.cell_size - touch.pos[1]) / self.cell_size)
            idx = min(grid_layout.cols * max(0, y - 1) + x, cnt_max)

            i = int(cnt_max - idx)

            self.temp_idx = idx

            if i > 0:
                grid_layout.add_widget(self, i)
            else:
                last_child = grid_layout.children[0]
                if isinstance(last_child, EOLItem):
                    grid_layout.add_widget(self, 1)
                    self.temp_idx = cnt_max - 1
                else:
                    grid_layout.add_widget(self)

        return super(DraggableItem, self).on_touch_move(touch, *args)

    def on_touch_up(self, touch, *args):
        if touch.grab_current == self:
            self.thumb.center = touch.pos
            self.container.remove_widget(self.thumb)
            self.add_widget(self.thumb)
            touch.ungrab(self)
            self.container.on_image_touch_up(self, self.temp_idx)
            self.temp_idx = None
            return True

        return super(DraggableItem, self).on_touch_up(touch, *args)

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
