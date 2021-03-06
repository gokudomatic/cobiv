from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.scrollview import ScrollView

from cobiv.modules.core.hud import Hud

Builder.load_string('''
#: import Window kivy.core.window.Window
<Sidebar>:
    item_list: item_list_layout
    size_hint: (1,1)
    StackLayout:
        id: item_list_layout
        size_hint: (1,None)
        minimum_height: self.height
''')


class Sidebar(Hud, ScrollView):
    item_list = ObjectProperty(None)
    enabled = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(Sidebar, self).__init__(**kwargs)
        self.session = self.get_session()
        self.bind(enabled=self.set_enabled)

    def set_enabled(self, instance, value):
        if value:
            self.bind_cursor()
        else:
            self.unbind_cursor()

    def bind_cursor(self):
        if self.session is not None:
            self.session.cursor.bind(file_id=self.on_file_id_change)
            self.refresh_widgets()

    def unbind_cursor(self):
        if self.session is not None:
            self.session.cursor.unbind(file_id=self.on_file_id_change)

    def on_file_id_change(self, instance, value):
        self.refresh_widgets()

    def refresh_widgets(self):
        for c in self.item_list.children:
            refresh = getattr(c, 'refresh', None)
            if refresh is not None:
                c.refresh()


Factory.register('SimpleSidebar', cls=Sidebar)
