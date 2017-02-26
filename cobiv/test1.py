import math
from kivy.app import App

from kivy.uix.image import Image
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.clock import Clock


from os import listdir

from cobiv.libs.magnet import Magnet

IMAGEDIR = 'C:\\Users\\edwin\\Pictures\\'

IMAGES = filter(
    lambda x: x.endswith('.jpg'),
    listdir(IMAGEDIR))

CELL_SIZE=256

kv = '''
#:import win kivy.core.window
#:import math math

FloatLayout:
    BoxLayout:
        ScrollView:
            id: scroll_view
            GridLayout:
                id: grid_layout
                cell_size: 128
                cols: int(self.width/self.cell_size)
                size_hint: None,None
                width: win.Window.width
                height: int(self.cell_size * math.ceil(1+len(self.children)/self.cols))
'''


class DraggableImage(Magnet):
    img = ObjectProperty(None, allownone=True)
    app = ObjectProperty(None)

    def on_img(self, *args):
        self.clear_widgets()

        if self.img:
            Clock.schedule_once(lambda *x: self.add_widget(self.img), 0)

    def on_touch_down(self, touch, *args):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.remove_widget(self.img)
            self.app.root.add_widget(self.img)

            abs_pos=self.app.root.ids.scroll_view.to_parent(touch.pos[0],touch.pos[1])

            self.img.center = abs_pos

            return True

        return super(DraggableImage, self).on_touch_down(touch, *args)

    def on_touch_move(self, touch, *args):
        grid_layout = self.app.root.ids.grid_layout

        if touch.grab_current == self:
            abs_pos=self.app.root.ids.scroll_view.to_parent(touch.pos[0],touch.pos[1])

            self.img.center = abs_pos

            grid_layout.remove_widget(self)

            cnt_max = len(grid_layout.children)
            idx=min(grid_layout.cols*math.floor((grid_layout.height-touch.pos[1])/CELL_SIZE)+math.floor(touch.pos[0]/CELL_SIZE),cnt_max)

            i=int(cnt_max-idx)

            if i>0:
                grid_layout.add_widget(self, i )
            else:
                grid_layout.add_widget(self)

        return super(DraggableImage, self).on_touch_move(touch, *args)

    def on_touch_up(self, touch, *args):
        if touch.grab_current == self:
            self.img.center=touch.pos
            self.app.root.remove_widget(self.img)
            self.add_widget(self.img)
            touch.ungrab(self)
            return True

        return super(DraggableImage, self).on_touch_up(touch, *args)


class DnDMagnet(App):
    def build(self):
        self.root = Builder.load_string(kv)
        self.root.ids.grid_layout.cell_size=CELL_SIZE
        cnt=0
        for i in IMAGES:
            cnt+=1

            image = Image(source=IMAGEDIR + i, size=(CELL_SIZE, CELL_SIZE),
                          size_hint=(None, None))
            draggable = DraggableImage(img=image, app=self,
                                       size_hint=(None, None),
                                       size=(CELL_SIZE, CELL_SIZE))
            self.root.ids.grid_layout.add_widget(draggable)

        return self.root


if __name__ == '__main__':
    DnDMagnet().run()