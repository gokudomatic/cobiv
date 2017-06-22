import os
import unittest
from functools import partial
from time import sleep

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout

from cobiv.modules.browser.browser import Browser
from cobiv.modules.session.Session import Session
from cobiv.modules.sqlitedb.sqlitedb import SqliteDb

from kivy.core.window import Window

Window.size = (360, 360)


class TestMainWidget(GridLayout):
    def execute_cmd(self, action, *args, **kwargs):
        if action == "load-set":
            self.browser.load_set()
        elif action == "refresh-marked":
            self.browser.refresh_mark()
        else:
            pass

    def show_progressbar(self, *args, **kwargs):
        pass

    def set_progressbar_value(self, *args, **kwargs):
        pass

    def close_progressbar(self, *args, **kwargs):
        pass

    def set_browser(self, instance):
        self.browser = instance
        self.add_widget(instance)


class TestApp(App):
    session = None

    def __init__(self, **kwargs):
        super(TestApp, self).__init__(**kwargs)
        self.configuration = {
            'thumbnails.path': '',
            'repository': 'images',
            'thumbnails.path': self.get_user_path('thumbs')
        }

    def build(self):
        return TestMainWidget(size_hint=(1, 1), cols=1)

    def get_config_value(self, key, default=""):
        if self.configuration.has_key(key):
            return self.configuration[key]
        else:
            return default

    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    def lookup(self, object_name, category):
        if category == "Entity" and object_name == "session":
            return self.session
        else:
            return None


class BrowserTest(unittest.TestCase):
    def setUp(self):
        Clock._events = [[] for i in range(256)]

    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    def prepare_browser(self, app):
        app.session = Session()

        db = SqliteDb()
        db.init_test_db()
        db.session = app.session

        b = Browser()

        app.root.set_browser(b)
        b.ready()
        b.on_switch(loader_thread=False)

        sleep(0.1)
        Clock.tick()

        return b, db

    def proceed_search(self,db,query=None):
        if query is not None:
            db.search_tag(query)
        else:
            db.search_tag()
        sleep(0.1)
        for i in range(2):
            Clock.tick()

    def _test_initialization(self, app, *args):
        b, db = self.prepare_browser(app)
        self.assertEqual(0, len(b.image_queue))

        self.assertEqual(len(b.grid.children), 1)
        self.assertItemsEqual((360, 360), Window.size)
        self.assertItemsEqual((1, 1), b.size_hint)
        self.assertItemsEqual((360, 360), b.size)

        app.stop()


    def _test_load_set(self, app, *args):
        b, db = self.prepare_browser(app)
        self.assertEqual(0, len(b.image_queue))

        db.search_tag()
        sleep(0.1)
        Clock.tick()
        self.assertEqual(27, len(b.image_queue))

        for i in range(27):
            self.assertEqual("images\\%04d.jpg" % (i + 1,), b.image_queue[i][3])
        Clock.tick()

        self.assertEqual(len(b.grid.children), 27)

        self.assertFalse(b.cursor.is_eol())
        self.assertEqual(b.page_cursor.pos,b.cursor.pos)

        app.stop()

    def _test_basic_moves(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)

        cursor=b.cursor
        for i in range(10):
            b.select_next(0)
            Clock.tick()
            self.assertEqual(i+1,cursor.pos)
            self.assertFalse(b.cursor.is_eol())
            self.assertNotEqual(b.page_cursor.pos,b.cursor.pos)
        for i in range(10):
            b.select_previous(0)
            Clock.tick()
            self.assertEqual(10-i-1,cursor.pos)
            self.assertFalse(b.cursor.is_eol())
        self.assertEqual(b.page_cursor.pos,b.cursor.pos)

        b.select_down(0)
        Clock.tick()
        self.assertEqual(3, cursor.pos)
        b.select_next(0)
        b.select_down(0)
        Clock.tick()
        self.assertEqual(7, cursor.pos)
        b.select_next(0)
        b.select_up(0)
        Clock.tick()
        self.assertEqual(5, cursor.pos)
        b.select_up(0)
        Clock.tick()
        self.assertEqual(2, cursor.pos)
        b.select_up(0)
        Clock.tick()
        self.assertEqual(0, cursor.pos)

        app.stop()

    def _test_load_more(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        for i in range(7):
            b.select_down(0)
            Clock.tick()

        self.assertEqual(0,b.page_cursor.pos)
        self.assertEqual(21,cursor.pos)

        b.select_down(0)
        Clock.tick()
        self.assertEqual(3,b.page_cursor.pos)
        self.assertEqual(24,cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        for i in range(23):
            b.select_down(0)
            Clock.tick()
        self.assertEqual(93,cursor.pos)
        self.assertEqual(72,b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        b.select_down(0)
        Clock.tick()
        self.assertEqual(96,cursor.pos)
        self.assertEqual(75,b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        b.select_down(0)
        Clock.tick()

        self.assertEqual(99,cursor.pos)
        self.assertEqual(75,b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        b.select_down(0)
        Clock.tick()
        self.assertEqual(100,cursor.pos)
        self.assertTrue(cursor.is_eol())
        self.assertEqual(len(b.grid.children), 26)
        self.assertEqual(75,b.page_cursor.pos)

        # moving up
        b.select_up(0)
        Clock.tick()
        self.assertEqual(75,b.page_cursor.pos)
        self.assertEqual(97,cursor.pos)
        self.assertFalse(cursor.is_eol())

        for i in range(32):
            b.select_up(0)
            Clock.tick()
        self.assertEqual(0,b.page_cursor.pos)
        self.assertEqual(1,cursor.pos)

        b.select_up(0)
        Clock.tick()

        self.assertEqual(0,b.page_cursor.pos)
        self.assertEqual(0,cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        app.stop()


    def _test_go(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        # go same pos
        b.select_next(0)
        b.select_custom(cursor.pos)
        self.assertEqual(1,cursor.pos)
        self.assertEqual("images\\0002.jpg",cursor.filename)
        self.assertEqual(0,b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # go same page
        b.select_custom(8)
        Clock.tick()
        self.assertEqual(8,cursor.pos)
        self.assertEqual("images\\0009.jpg",cursor.filename)
        self.assertEqual(0,b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # go end of current page
        b.select_custom(25)
        Clock.tick()
        self.assertEqual(25,cursor.pos)
        self.assertEqual("images\\0026.jpg",cursor.filename)
        self.assertEqual(3,b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # go another page
        b.select_custom(70)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(70,cursor.pos)
        self.assertEqual("images\\0071.jpg",cursor.filename)
        self.assertEqual(54,b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)


        # go multiple times
        b.select_custom(5)
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        b.select_custom(40)
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        b.select_custom(80)
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        self.assertEqual(80,cursor.pos)
        self.assertEqual("images\\0081.jpg",cursor.filename)
        self.assertEqual(66,b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        app.stop()

    def _test_first_last(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        # test first / same page
        for i in range(5):
            b.select_first()
            Clock.tick()
        self.assertEqual(0,cursor.pos)
        self.assertEqual("images\\0001.jpg",cursor.filename)
        self.assertEqual(0,b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        for i in range(5):
            for j in range(i+1):
                b.select_next(0)
            b.select_first()
            Clock.tick()

            self.assertEqual(0,cursor.pos)
            self.assertEqual("images\\0001.jpg",cursor.filename)
            self.assertEqual(0,b.page_cursor.pos)
            self.assertEqual(len(b.grid.children), 27)

        # test first / other page
        b.select_custom(60)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(len(b.grid.children), 27)

        b.select_first()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(0, cursor.pos)
        self.assertEqual("images\\0001.jpg", cursor.filename)
        self.assertEqual(0, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # test last
        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(99, cursor.pos)
        self.assertEqual("images\\0100.jpg", cursor.filename)
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        b.select_previous(0)
        b.select_previous(0)
        b.select_previous(0)
        self.assertEqual(96, cursor.pos)
        self.assertEqual("images\\0097.jpg", cursor.filename)
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)
        Clock.tick()
        b.select_last()
        Clock.tick()
        self.assertEqual(99, cursor.pos)
        self.assertEqual("images\\0100.jpg", cursor.filename)
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)


        app.stop()

    def _test_eol_basic(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        # test previous & next
        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        b.select_next(0)
        Clock.tick()
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        for i in range(5):
            b.select_next(0)
            Clock.tick()
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        b.select_previous(0)
        Clock.tick()
        self.assertEqual(99, cursor.pos)
        self.assertEqual("images\\0100.jpg", cursor.filename)
        self.assertFalse(cursor.is_eol())
        self.assertEqual(75, b.page_cursor.pos)

        b.select_next(0)
        Clock.tick()
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())


        # test up & bottom
        b.select_up(0)
        Clock.tick()
        self.assertEqual(97, cursor.pos)
        self.assertEqual("images\\0098.jpg", cursor.filename)
        self.assertFalse(cursor.is_eol())
        self.assertEqual(75, b.page_cursor.pos)

        for i in range(3):
            b.select_down(0)
            Clock.tick()
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())

        # test first & last

        b.select_last()
        Clock.tick()
        self.assertEqual(99, cursor.pos)
        self.assertEqual("images\\0100.jpg", cursor.filename)
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        b.select_next(0)
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())

        b.select_first()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(0, cursor.pos)
        self.assertEqual("images\\0001.jpg", cursor.filename)
        self.assertEqual(0, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # test custom go
        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        b.select_next(0)
        Clock.tick()
        self.assertEqual(100, cursor.pos)

        b.select_custom(50)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(50, cursor.pos)
        self.assertEqual("images\\0051.jpg", cursor.filename)
        self.assertEqual(36, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        app.stop()

    def _test_mark(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        marked=[e.position for e in b.grid.children if e.is_marked()]
        self.assertEqual(0,len(marked))

        b.select_custom(3)
        b.mark_current(True)

        for i in range(3):
            b.select_next(0)
            b.select_next(0)
            # Clock.tick()
            b.mark_current(True)

        self.assertEqual(4,cursor.get_marked_count())
        marked=[e.position for e in b.grid.children if e.is_marked()]
        self.assertItemsEqual([3,5,7,9],marked)

        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        marked=[e.position for e in b.grid.children if e.is_marked()]
        self.assertItemsEqual([],marked)


        b.select_first()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        marked=[e.position for e in b.grid.children if e.is_marked()]
        self.assertItemsEqual([3,5,7,9],marked)

        b.select_custom(5)
        b.mark_current()

        # test load more
        for i in range(11):
            b.select_down(0)
            Clock.tick()

        marked=[e.position for e in b.grid.children if e.is_marked()]
        self.assertItemsEqual([],marked)

        # test load more
        for i in range(10):
            b.select_up(0)
            Clock.tick()

        marked=[e.position for e in b.grid.children if e.is_marked()]
        self.assertItemsEqual([3,7,9],marked)

        cursor.mark_all()
        b.refresh_mark()
        marked=[e.position for e in b.grid.children if e.is_marked()]
        self.assertEqual(27,len(marked))

        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        marked=[e.position for e in b.grid.children if e.is_marked()]
        self.assertEqual(25,len(marked))

        app.stop()

    def _test_cut(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        self.assertTrue(False)
        # test load more

        # test load set

        # test first

        # test last

        # test multiple cut

        # test cut all

        app.stop()

    def _test_paste(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        self.assertTrue(False)

        # test simple cut and paste

        # test first paste

        # test last paste

        # test multiple cut

        # test cut and paste all

        app.stop()

    def _test_eol_yank(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        self.assertTrue(False)

        # test cut

        # test paste

        app.stop()

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def test_01_initialization(self):
        self.call_test(self._test_initialization)

    def test_02_load_set(self):
        self.call_test(self._test_load_set)

    def test_03_basic_moves(self):
        self.call_test(self._test_basic_moves)

    def test_04_load_more(self):
        self.call_test(self._test_load_more)

    def test_05_go(self):
        self.call_test(self._test_go)

    def test_06_first_last(self):
        self.call_test(self._test_first_last)

    def test_07_eol(self):
        self.call_test(self._test_eol_basic)

    def test_08_mark(self):
        self.call_test(self._test_mark)

    def test_17_cut(self):
        self.call_test(self._test_cut)

    def test_18_paste(self):
        self.call_test(self._test_paste)

    def test_19_eol_yank(self):
        self.call_test(self._test_eol_yank)

if __name__ == "__main__":
    unittest.main()
