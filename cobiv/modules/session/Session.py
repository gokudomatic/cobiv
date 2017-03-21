from kivy.properties import NumericProperty

from cobiv.modules.entity import Entity
from cobiv.modules.imageset.ImageSet import ImageSet
from cobiv.modules.session.cursor import Cursor


class Session(Entity):

    cursor = Cursor()

    def __init__(self):
        pass
