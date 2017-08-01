from kivy.factory import Factory
from kivy.uix.label import Label

from cobiv.modules.browser.widgets.labelwidget import LabelWidget
from cobiv.modules.component import Component


class TagsWidget(LabelWidget, Component):
    limit = -1

    def __init__(self, **kwargs):
        super(TagsWidget, self).__init__(**kwargs)
        if kwargs.has_key('limit'):
            self.limit = kwargs['limit']

    def refresh(self):
        text = ""
        tags = self.session.cursor.get_tags()
        if tags is not None and len(tags) > 0:
            count = 0
            for key in tags[1]:
                if len(text) > 1:
                    text += '\n'

                count += 1
                if count > self.limit > 0:
                    text += '...'
                    break
                else:
                    value = tags[1][key]
                    text += (key + ":" + value) if key != "tag" else value
        self.text = text


Factory.register('TagsWidget', cls=TagsWidget)
