from kivy.app import App
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import StringProperty
from kivy.uix.image import AsyncImage

from modules.views.browser.ThumbnailImage import ThumbnailImage

Builder.load_string('''
#:import F kivy.factory.Factory
#:import Window kivy.core.window.Window

<PinchDetector>:        
    ScrollView:
        id: scroller

''')

class PinchDetector(Factory.FloatLayout,object):

    source = StringProperty('c:/Users/edwin/Pictures/gandalf.png')

    def __init__(self):
        super(PinchDetector, self).__init__()
        img = ThumbnailImage(source=self.source, mipmap=True, allow_stretch=True, keep_ratio=True)
        self.ids.scroller.add_widget(img)


class TestApp(App):

    def build(self):
        self.root=PinchDetector()
        return self.root


if __name__ == '__main__':
    TestApp().run()
