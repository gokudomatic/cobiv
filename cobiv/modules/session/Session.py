from kivy.properties import NumericProperty

from cobiv.modules.entity import Entity
from cobiv.modules.imageset.ImageSet import ImageSet


class Session(Entity):
    current_imageset = ImageSet()

    current_imageset_index = NumericProperty(None)

    def __init__(self):
        pass

    def get_currentset(self):
        return self.current_imageset
