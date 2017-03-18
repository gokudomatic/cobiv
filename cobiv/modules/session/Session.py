from kivy.properties import NumericProperty

from cobiv.modules.entity import Entity
from cobiv.modules.imageset.ImageSet import ImageSet
from cobiv.modules.session.cursor import Cursor


class Session(Entity):
    current_imageset = ImageSet()

    current_imageset_index = NumericProperty(None)

    cursor = Cursor()

    def __init__(self):
        pass

    def get_currentset(self):
        return self.current_imageset

    def get_current_image(self):
        if self.current_imageset_index == None or len(self.current_imageset) == 0:
            return None
        return self.current_imageset.uris[self.current_imageset_index]
