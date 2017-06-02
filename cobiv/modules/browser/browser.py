from collections import deque

import datetime
from kivy.app import App
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView

from cobiv.modules.browser.eolitem import EOLItem
from cobiv.modules.browser.item import Item
from cobiv.modules.browser.thumbloader import ThumbLoader
from cobiv.modules.component import Component
from cobiv.modules.view import View
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
import os

Builder.load_file('modules/browser/browser.kv')


class VerticalLoadEffect(DampedScrollEffect):
    def __init__(self, **kwargs):
        super(VerticalLoadEffect, self).__init__(**kwargs)
        self.trigger_load_next = Clock.create_trigger(self.load_next, 0.5)
        self.trigger_load_previous = Clock.create_trigger(self.load_prev, 0.5)

    def on_overscroll(self, *args):
        super(VerticalLoadEffect, self).on_overscroll(*args)
        if self.overscroll < -50:
            self.trigger_load_previous()
        elif self.overscroll > 50:
            self.trigger_load_next()

    def load_prev(self, dt):
        App.get_running_app().root.get_view().load_more(factor=3, direction_next=False)

    def load_next(self, dt):
        App.get_running_app().root.get_view().load_more(factor=3)


class ThumbScrollView(ScrollView):
    def __init__(self, **kwargs):
        super(ThumbScrollView, self).__init__(**kwargs)
        self.effect_y = VerticalLoadEffect()


class Browser(View, FloatLayout):
    cursor = None
    page_cursor = None
    eol_cursor = None
    selected_image = None
    grid = ObjectProperty(None)

    cell_size = NumericProperty(120)
    page_rows = NumericProperty(None)
    max_rows = NumericProperty(None)
    max_scroll_ratio = NumericProperty(3)
    max_items_cache = NumericProperty(None)

    global_scroll_pos = NumericProperty(0)
    session = None
    image_queue = deque()
    append_queue = True
    pending_actions = deque()
    widget_to_scroll = None
    thumb_loader = None

    def __init__(self, **kwargs):
        super(Browser, self).__init__(**kwargs)

        self.tg_select_next = Clock.create_trigger(self.select_next, 0.1)
        self.tg_select_previous = Clock.create_trigger(self.select_previous, 0.1)
        self.tg_select_up = Clock.create_trigger(self.select_up, 0.1)
        self.tg_select_down = Clock.create_trigger(self.select_down, 0.1)
        self.tg_load_set = Clock.create_trigger(self.trigger_load_set, 0.1)

        self.set_action("load-set", self.load_set)
        self.set_action("next", self.tg_select_next)
        self.set_action("down", self.tg_select_down)
        self.set_action("previous", self.tg_select_previous)
        self.set_action("up", self.tg_select_up)
        self.set_action("mark", self.mark_current)
        self.set_action("refresh-marked", self.refresh_mark)
        self.set_action("first", self.select_first)
        self.set_action("last", self.select_last)
        self.set_action("g", self.select_custom)
        self.set_action("cut-marked", self.cut_marked)
        self.set_action("paste-marked", self.paste_marked)

    def get_name(self=None):
        return "browser"

    def build_yaml_config(self, config):
        config[self.get_name()] = {
            'hotkeys': [
                {'key': '273', 'binding': 'up'},
                {'key': '274', 'binding': 'down'},
                {'key': '275', 'binding': 'next'},
                {'key': '276', 'binding': 'previous'},
                {'key': '103', 'binding': 'first'},
                {'key': '103', 'binding': 'last', 'modifiers': 1},
                {'key': '32', 'binding': 'mark'},
                {'key': '13', 'binding': 'switch-view viewer'},
                {'key': '97', 'binding': 'mark-all'},
                {'key': '105', 'binding': 'mark-invert'},
                {'key': '120', 'binding': 'cut-marked'},
                {'key': '112', 'binding': 'paste-marked'}
            ],
            'cache': {
                'thumbnails': {
                    'size': 500
                }
            },
            'grid': {
                'icon_size': 120
            }
        }
        return config

    def ready(self):
        Component.ready(self)
        self.thumbs_path = self.get_global_config_value('thumbnails.path')

        self.cell_size = self.get_config_value('grid.icon_size', 120)

        self.session = self.get_app().lookup("session", "Entity")
        self.cursor = self.session.cursor

        self.thumb_loader = ThumbLoader()
        self.thumb_loader.container = self

    def on_switch(self):
        self.cursor.bind(file_id=self.on_id_change)
        self.load_set()
        if self.selected_image is not None:
            Clock.schedule_once(self.scroll_to_image)
        self.thumb_loader.restart()

        self.bind(max_rows=self.on_size_change, width=self.on_size_change)

    def on_switch_lose_focus(self):
        self.cursor.unbind(file_id=self.on_id_change)
        self.unbind(max_rows=self.on_size_change, width=self.on_size_change)
        self.thumb_loader.stop()

    def scroll_to_image(self, dt):
        self.ids.scroll_view.scroll_to(self.selected_image)

    def on_size_change(self, source, size):
        if self.cursor.filename is None:
            return
        diff_amount = self.max_items() - len(self.grid.children)
        if diff_amount > 0:
            self.load_more(factor=0, recenter=True)
            self.pending_actions.append(self._scroll_on_widget)
        elif diff_amount < 0:
            self.pending_actions.append(self._remove_recenter)
            self.pending_actions.append(self._scroll_on_widget)
            self.do_next_action()

    def max_items(self):
        return self.grid.cols * self.max_rows

    #########################################################

    def load_set(self):
        self.tg_load_set()

    def trigger_load_set(self, dt):
        self.grid.clear_widgets()

        if self.cursor.file_id is not None:
            self.start_progress("Loading thumbs...")
            self.pending_actions.append(self._load_set)
            self.pending_actions.append(self._load_process)
            self.do_next_action(immediat=True)
        else:
            e = EOLItem(cell_size=self.cell_size, container=self)
            self.grid.add_widget(e)
            e.selected = True
            self.cursor.go_eol()
            self.page_cursor = self.cursor.clone()

    def _load_set(self, dt):
        max_count = self.max_items()
        self.set_progress_max_count(max_count)
        self.reset_progress()

        start_pos = max(0, self.cursor.pos - max_count / 2)
        diff = start_pos % self.grid.cols
        start_pos -= diff

        self.page_cursor = self.cursor.get_cursor_by_pos(start_pos)

        c = self.cursor.get_cursor_by_pos(self.page_cursor.pos)
        self.append_queue = True

        list_ids = c.get_next_ids(self.max_items_cache * self.grid.cols, self_included=True)

        idx = 0
        for id_file, position, filename in list_ids:

            if idx < max_count:

                self.thumb_loader.append((id_file, filename))

                thumb_filename = os.path.join(self.thumbs_path, str(id_file) + '.png')

                self.image_queue.append((thumb_filename, id_file, position, filename))

            else:
                self.thumb_loader.append((id_file, filename))

            idx += 1

        if len(list_ids) < max_count:
            self.image_queue.append((None, None, "eol", None))
        if idx > 0:

            self.reset_progress()
            self.do_next_action()
        else:
            pass

    def _load_process(self, dt):
        queue_len = len(self.image_queue)
        if queue_len > 0:
            marked_list = self.page_cursor.get_all_marked()

            for i in range(queue_len):
                thumb_filename, file_id, pos, image_filename = self.image_queue.popleft()

                if pos == "eol":
                    e = EOLItem(cell_size=self.cell_size, container=self)
                    self.grid.add_widget(e)
                else:

                    thumb = self.thumb_loader.get_image(file_id, thumb_filename, image_filename)

                    item = Item(thumb=thumb, container=self,
                                cell_size=self.cell_size, file_id=file_id, position=pos, duration=0)

                    if file_id == self.cursor.file_id:
                        self.selected_image = item
                        item.set_selected(True)

                    if file_id in marked_list:
                        item.set_marked(True)

                    if self.append_queue:
                        self.grid.add_widget(item)
                    else:
                        self.grid.add_widget(item, len(self.grid.children))

                    self.tick_progress()

            if len(self.image_queue) > 0:
                Clock.schedule_once(self._load_process, 0)

        self.stop_progress()
        self.do_next_action(immediat=True)

    ####################################################

    def select_next(self, dt):
        if self.cursor.filename is not None:
            if self.cursor.go_next():
                last_child = self.grid.children[0]
                if not isinstance(last_child, EOLItem):
                    if last_child.position - self.grid.cols < self.cursor.pos:
                        self.load_more()
            else:
                self.select_EOL()

    def select_previous(self, dt):
        if self.cursor.filename is not None or self.cursor.is_eol():
            self.cursor.go_previous()
            if not isinstance(self.grid.children[-1], EOLItem):
                if self.grid.children[-1].position + self.grid.cols > self.cursor.pos:
                    self.load_more(direction_next=False)

    def select_down(self, dt):
        if self.cursor.filename is not None:
            if not self.select_row(1):
                # self.cursor.go_last()
                self.select_EOL()

    def select_up(self, dt):

        if self.cursor.filename is not None or self.cursor.is_eol():
            if not self.select_row(-1):
                self.cursor.go_first()

    def select_first(self):
        if self.cursor.filename is not None or self.cursor.is_eol():
            self.thumb_loader.clear_cache()
            self.cursor.go_first()

    def select_last(self):
        if self.cursor.filename is not None:
            self.thumb_loader.clear_cache()
            self.cursor.go_last()

    def select_custom(self, position=None):
        if (self.cursor.filename is not None or self.cursor.is_eol) and position is not None:
            self.thumb_loader.clear_cache()
            self.cursor.go(position)

    def select_row(self, diff):
        if self.page_cursor.is_eol():
            return

        pos = self.cursor.pos - self.page_cursor.pos

        nb_cols = self.grid.cols

        linenr = pos / nb_cols
        colnr = pos % nb_cols
        new_pos = colnr + (linenr + diff) * nb_cols

        print self.page_cursor.pos

        if new_pos >= len(self.grid.children) - nb_cols:
            print "loading more next"
            self.load_more()
        elif new_pos <= nb_cols:
            print "loading more previous"
            self.load_more(direction_next=False)

        return self.cursor.go(self.page_cursor.pos + new_pos)

    def select_EOL(self):
        self.cursor.go_eol()

    def on_id_change(self, instance, value):
        if self.selected_image is not None:
            self.selected_image.set_selected(False)

        if self.cursor.is_eol():
            last_item = self.grid.children[0]
            if isinstance(last_item, EOLItem):
                last_item.set_selected(True)
                self.selected_image = last_item
        elif self.cursor.filename is None or self.cursor.filename == '' or value is None or len(
                self.grid.children) == 0:
            self.selected_image = None
        else:
            thumbs = [image for image in self.grid.children if image.file_id == value]
            if len(thumbs) > 0:
                item = thumbs[0]
                item.set_selected(True)
                self.selected_image = item
                self.ids.scroll_view.scroll_to(item)
            else:
                self.load_set()
                self.pending_actions.append(self._pass)
                self.pending_actions.append(self._scroll_on_widget)

    def on_image_touch_up(self, img, idx):
        # select item
        c = self.cursor.get_cursor_by_pos(img.position)
        if idx is not None:
            c.move_to(idx + self.page_cursor.pos)
            self.refresh_positions()
        self.cursor.go(c.pos)

    def refresh_positions(self):
        list_id = [item.file_id for item in self.grid.children]
        mapping = self.cursor.get_position_mapping(list_id)
        for item in self.grid.children:
            for m in mapping:
                if m[0] == item.file_id:
                    item.position = m[1]
                    break

    def load_more(self, direction_next=True, factor=1, recenter=False):
        if len(self.grid.children) == 0:
            self.do_next_action()
            return

        if not direction_next and self.page_cursor.pos == 0:
            self.do_next_action()
            return

        if direction_next:
            last_child = self.grid.children[0]
            if isinstance(last_child, EOLItem):
                last_pos = None
            else:
                last_pos = last_child.position
        else:
            last_pos = self.grid.children[-1].position

        self.image_queue.clear()
        self.append_queue = direction_next
        if last_pos is not None:
            c = self.cursor.get_cursor_by_pos(last_pos)

            to_load = self.grid.cols * factor + max(0, self.max_items() - len(self.grid.children))
            to_cache = self.max_items_cache * self.grid.cols

            do_add_eol = False
            if direction_next:
                list_id = c.get_next_ids(to_cache)
                do_add_eol = len(list_id) < to_load
            else:
                list_id = c.get_previous_ids(to_cache)

            idx = 0
            for id_file, position, filename in list_id:
                if idx < to_load:
                    thumb_filename = os.path.join(self.thumbs_path, str(id_file) + '.png')
                    self.image_queue.append((thumb_filename, id_file, position, filename))
                else:
                    self.thumb_loader.append((id_file, filename))
                idx += 1

            if do_add_eol:
                self.image_queue.append((None, None, "eol", None))

        if len(self.image_queue) > 0:
            self.pending_actions.append(self._load_process)
            if recenter:
                self.pending_actions.append(self._remove_recenter)
            else:
                if direction_next:
                    self.pending_actions.append(self._remove_firsts)
                else:
                    self.pending_actions.append(self._remove_lasts)
            self.do_next_action()
        else:
            self.stop_progress()

    def do_next_action(self, immediat=False, timeout=0):
        if len(self.pending_actions) > 0:
            action = self.pending_actions.popleft()
            if immediat:
                action(0)
            else:
                Clock.schedule_once(action, timeout)

    def _remove_firsts(self, dt):
        child_count = len(self.grid.children)
        to_remove = int(child_count - self.max_items())
        if to_remove > 0:
            for i in range(to_remove):
                widget = self.grid.children[-1]
                self.grid.remove_widget(widget)
                widget.clear_widgets()

            widget = self.grid.children[-1]
            self.page_cursor.go(widget.position)
            if self.cursor.pos < self.page_cursor.pos:
                self.cursor.go(self.grid.children[0].position)
        self.do_next_action()

    def _remove_lasts(self, dt):
        to_remove = int(len(self.grid.children) - self.max_items())
        if to_remove > 0:
            for i in range(to_remove):
                widget = self.grid.children[0]
                self.grid.remove_widget(widget)
                widget.clear_widgets()

            widget = self.grid.children[-1]
            self.page_cursor.go(widget.position)
            if self.cursor.pos > self.grid.children[0].position:
                self.cursor.go(self.grid.children[-1].position)

        self.do_next_action()

    def _remove_recenter(self, dt):
        total_to_remove = len(self.grid.children) - self.max_items()
        if total_to_remove > 0:
            current_local_pos = self.cursor.pos - self.page_cursor.pos
            # remove first items
            to_delete_before = current_local_pos - self.max_items() / 2
            to_delete_after = len(self.grid.children) - (current_local_pos + self.max_items() / 2)
            if to_delete_after < 0:
                # it means we're at the end of the list
                to_delete_before += to_delete_after
            if to_delete_before > 0:
                for i in range(to_delete_before):
                    widget = self.grid.children[-1]
                    self.grid.remove_widget(widget)
                    widget.clear_widgets()

            # remove last items
            self._remove_lasts(0)
            widget = self.grid.children[-1]
            self.page_cursor.go(widget.position)

        self.do_next_action()

    def _pass(self, dt):
        self.do_next_action(timeout=0.3)

    def _scroll_on_widget(self, dt):
        if self.widget_to_scroll is None:
            self._scroll_to_current()
        else:
            self.ids.scroll_view.scroll_to(self.widget_to_scroll)
        self.do_next_action()

    def _scroll_to_current(self):
        if self.selected_image is not None:
            self.ids.scroll_view.scroll_to(self.selected_image)

    ##############################################################

    def mark_current(self, value=None):
        if self.selected_image is not None:
            self.cursor.mark(value)

    def refresh_mark(self):
        mapping = self.cursor.get_all_marked()
        for item in self.grid.children:
            item.set_marked(item.file_id in mapping)

    def cut_marked(self):
        if self.cursor.get_marked_count() == 0:
            return

        children = dict()
        for c in self.grid.children:
            children[c.file_id] = c

        self.execute_cmd("cut-marked", force_default=True)
        sql_size = len(self.cursor)
        if sql_size == 0:
            self.load_set()
        else:

            if isinstance(self.grid.children[0],EOLItem):
                item_before_eol=self.grid.children[1]
            else:
                item_before_eol=None

            mapping = self.cursor.get_position_mapping(children.keys())
            page_cursor_pos = None
            cursor_pos = None
            for file_id, position in mapping:
                if file_id == self.cursor.file_id:
                    cursor_pos = position
                elif file_id == self.page_cursor.file_id:
                    page_cursor_pos = position

                child = children[file_id]
                if position < 0:
                    self.grid.remove_widget(child)
                else:
                    child.position = position
            if len(self.grid.children) == 0:
                self.cursor.go(min(sql_size, self.cursor.pos))
                self.load_set()
            else:
                if page_cursor_pos < 0:
                    self.page_cursor.go(self.grid.children[-1])
                if cursor_pos < 0:
                    self.cursor.go(page_cursor_pos)

                if item_before_eol is not None and not item_before_eol in self.grid.children:
                    #last item disappeared. link with eol must be updated
                    self.cursor.update_eol_implementation()

                # recenter
                self.pending_actions.append(self._remove_recenter)
                self.do_next_action()

    def paste_marked(self):
        if self.cursor.is_eol():
            pos_to_send = "eol"
        elif self.cursor.filename is not None:
            pos_to_send = self.cursor.pos
        else:
            return

        self.execute_cmd("past-marked " + str(pos_to_send), force_default=True)

        if len(self.cursor) == 0:
            return

        if len(self.grid.children) == 0:
            self.load_set()
            return

        self.pending_actions.append(self._remove_recenter)
        self.do_next_action()
