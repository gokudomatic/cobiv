from modules.core.component import Component
from modules.core.entity import Entity


class SetManager(Entity):

    def __init__(self) -> None:
        super().__init__()

    def remove(self,id):
        pass

    def save(self,id):
        pass

    def rename(self,id,new_id):
        pass

    def load(self,id):
        pass

    def add_to_current(self,id):
        pass

    def remove_from_current(self,id):
        pass

    def get_list(self):
        pass

    def regenerate_default(self):
        pass

    def query_to_current_set(self,query):
        pass