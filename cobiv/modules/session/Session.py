from cobiv.modules.entity import Entity
from cobiv.modules.session.cursor import Cursor


class Session(Entity):

    cursor = None

    def __init__(self):
        self.cursor = Cursor()
