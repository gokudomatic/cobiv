from cobiv.modules.core.component import Component


class Datasource(Component):
    connection = None

    def get_connection(self):
        if self.connection is None:
            self.connection = self.create_connection()
        return self.connection

    def create_connection(self):
        return None
