from cobiv.modules.entity import Entity
from cobiv.modules.session.cursor import Cursor


class Session(Entity):

    cursor = Cursor()

    def __init__(self):
        pass
