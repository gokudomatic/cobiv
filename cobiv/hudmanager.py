import logging

from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivy.uix.relativelayout import RelativeLayout

Builder.load_string('''
<BaseHUD>:
    size_hint: None, None
    size: win.Window.size
''')


class BaseHUD(RelativeLayout):
    visible = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(BaseHUD, self).__init__(**kwargs)

        self.bind(visible=self.on_visible)
        self.bind(height=self.on_visible)

    def on_visible(self, instance, value):
        self.pos = (0, 0 if self.visible else self.height)


class NotificationHUD(BaseHUD):
    logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(NotificationHUD, self).__init__(**kwargs)
        self.visible = True
        self.renderers = {}

    def notify(self, key=None, renderer=None, **kwargs):
        if key is None and renderer is None and len(kwargs) == 0:
            self.logger.error("Notification cannot have no parameters")
            return
        if key is None:
            if renderer is None:
                instance=Factory.NotificationLabel(**kwargs)
            else:
                instance=renderer(**kwargs)
            self.add_widget(instance)
            instance.start()
        else:
            if key in self.renderers:
                self.renderers[key].update(**kwargs)
            else:
                if renderer is None:
                    instance = Factory.NotificationLabel(key=key,**kwargs)
                else:
                    instance = renderer(key=key,**kwargs)
                self.renderers[key] = instance
                self.add_widget(instance)
                instance.start()

    def on_notification_complete(self, key, instance):
        if key in self.renderers:
            self.renderers.pop(key)
        self.remove_widget(instance)
