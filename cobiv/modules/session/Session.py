from cobiv.modules.entity import Entity
from cobiv.modules.imageset.ImageSet import ImageSet


class Session(Entity):
    current_imageset = ImageSet()

    def __init__(self):
        pass

    def get_currentset(self):
        return self.current_imageset
