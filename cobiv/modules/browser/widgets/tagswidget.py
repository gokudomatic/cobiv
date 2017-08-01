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
        tags = self.session.cursor.get_tags()

        def build_text():
            text = ""
            if tags is not None and len(tags) > 0:
                count = 0
                for key in tags[1]:
                    values = tags[1][key]
                    for value in values:
                        if len(text) > 1:
                            text += '\n'

                        count += 1
                        if count > self.limit > 0:
                            text += '...'
                            return text
                        else:
                            text += (key + ":" + value) if key != "tag" else value
            return text

        self.text = build_text()


Factory.register('TagsWidget', cls=TagsWidget)
