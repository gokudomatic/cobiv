from kivy.factory import Factory

from cobiv.modules.core.component import Component
from cobiv.modules.hud_components.sidebar.widgets.labelwidget import LabelWidget


class TagsWidget(LabelWidget, Component):
    limit = -1

    def __init__(self, **kwargs):
        self.limit = kwargs.pop('limit', -1)
        super(TagsWidget, self).__init__(**kwargs)

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
