import logging

logging.basicConfig(level=logging.DEBUG)

import os
import shutil
import unittest
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

from cobiv.modules.core.session.Session import Session
from cobiv.modules.database.sqlitedb.sqlitedb import SqliteDb


class TestMainWidget(Widget):
    def execute_cmds(self, *args, **kwargs):
        pass

    def show_progressbar(self, *args, **kwargs):
        pass

    def set_progressbar_value(self, *args, **kwargs):
        pass

    def close_progressbar(self, *args, **kwargs):
        pass


class TestApp(App):
    def __init__(self, **kwargs):
        super(TestApp, self).__init__(**kwargs)
        self.configuration = {
            'thumbnails.path': '',
            'repositories': ['osfs://images'],
            'thumbnails.path': self.get_user_path('thumbs')
        }

    def build(self):
        return TestMainWidget()

    def get_config_value(self, key, defaultValue=""):
        if key in self.configuration:
            return self.configuration[key]
        else:
            return defaultValue

    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    def fire_event(self, *args):
        pass

    def lookups(self, category):
        return []


class SQLiteDbTest(unittest.TestCase):
    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    def setUp(self):
        self.session = Session()

        f_path = self.get_user_path('images', 'test.jpg')
        if os.path.exists(f_path):
            os.remove(f_path)

    def tearDown(self):
        f_path = self.get_user_path('images', 'test.jpg')
        if os.path.exists(f_path):
            os.remove(f_path)
        super(SQLiteDbTest, self).tearDown()

    def init_db(self):
        db = SqliteDb()
        db.init_test_db(self.session)
        db.session = self.session

        return db

    def init_db_with_tags(self):
        db = SqliteDb()
        db.init_test_db(self.session)

        db.search_tag()
        c = self.session.cursor

        c.add_tag("one", "o", "e", "adamanta")
        c.go_next()
        c.add_tag("two", "o", "t", "adablateno")
        c.go_next()
        c.add_tag("three", "t", "r", "e", "3", "genoblame")

        return db

    def init_db_with_categorized_tags(self):
        db = SqliteDb()
        db.init_test_db(self.session)
        db.session = self.session

        db.search_tag()
        c = self.session.cursor

        self.assertEqual("/0001.jpg", c.filename)
        c.add_tag("cat1:one", "o", "e", "cat1:3")
        c.go_next()
        self.assertEqual("/0002.jpg", c.filename)
        c.add_tag("cat2:two", "o", "t")
        c.go_next()
        self.assertEqual("/0003.jpg", c.filename)
        c.add_tag("cat1:three", "letter:t", "r", "e", "cat1:3")

        return db

    def init_db_with_numeric_date_tags(self):
        db = SqliteDb()
        db.init_test_db(self.session)
        db.session = self.session

        db.search_tag()
        c = self.session.cursor

        self.assertEqual("/0001.jpg", c.filename)
        c.add_tag("modification_date:1503439200.0", "width:159", "height:81")  # time=2017.08.23
        c.go_next()
        self.assertEqual("/0002.jpg", c.filename)
        c.add_tag("modification_date:1503845435.0", "width:39", "height:81")  # time=2017.08.27
        c.go_next()
        self.assertEqual("/0003.jpg", c.filename)
        c.add_tag("modification_date:1458169200.0", "width:60", "height:60")  # time=2016.03.17

        return db

    def _test_initialization(self, app, *args):
        db = SqliteDb()
        db.init_test_db(self.session)

        db.close_db()

        app.stop()

    def _test_search_all(self, app, *args):
        db = SqliteDb()
        db.init_test_db(self.session)
        db.session = self.session

        db.search_tag()
        c = self.session.cursor

        self.assertEqual(3, len(c))
        self.assertEqual("/0001.jpg", c.filename)
        c.go_next()
        self.assertEqual("/0002.jpg", c.filename)
        c.go_next()
        self.assertEqual("/0003.jpg", c.filename)

        db.close_db()
        app.stop()

    def _test_search_tag(self, app, *args):
        db = self.init_db_with_tags()
        c = self.session.cursor

        db.search_tag("one")
        self.assertEqual(1, len(c))

        db.search_tag("o")
        self.assertEqual(2, len(c))

        db.search_tag("o", "-one")
        self.assertEqual(1, len(c))
        self.assertEqual("/0002.jpg", c.filename)

        db.search_tag("o", "e")
        self.assertEqual(1, len(c))

        db.close_db()
        app.stop()

    def _test_update_file(self, app, *args):
        db = self.init_db_with_tags()
        c = self.session.cursor

        new_filename = self.get_user_path('images', 'test.jpg')

        shutil.copy(self.get_user_path('images', '0003.jpg'), new_filename)
        self.assertTrue(os.path.exists(new_filename))
        db.updatedb(sameThread=True)
        db.search_tag()
        self.assertEqual(4, len(c))

        os.remove(new_filename)
        db.updatedb(sameThread=True)
        db.search_tag()
        self.assertEqual(3, len(c))

        db.close_db()
        app.stop()

    def _test_update_tags(self, app, *args):

        new_filename = self.get_user_path('images', 'test.jpg')
        shutil.copy(self.get_user_path('images', '0003.jpg'), new_filename)

        db = self.init_db_with_tags()
        c = self.session.cursor

        fs = self.session.get_filesystem(1)

        test_id = db.conn.execute('select id from file where name="/test.jpg"').fetchone()[0]

        # test when nothing changed
        self.assertCountEqual([], db._check_modified_files(repo_id=1, repo_fs=fs))
        db.update_tags(repo_id=1, repo_fs=fs)

        db.search_tag()
        c.go_last()
        c.get_tags()
        self.assertEqual(os.path.getsize(new_filename), c.get_tags()[0]['size'][0])
        self.assertEqual(os.path.getsize(self.get_user_path('images', '0003.jpg')), c.get_tags()[0]['size'][0])

        # test when file content changed
        shutil.copy(self.get_user_path('images', '0001.jpg'), new_filename)
        self.assertCountEqual([(test_id, '/test.jpg')], db._check_modified_files(repo_id=1, repo_fs=fs))
        db.update_tags(repo_id=1, repo_fs=fs)
        c.reload()
        self.assertEqual(os.path.getsize(new_filename), c.get_tags()[0]['size'][0])
        self.assertEqual(os.path.getsize(self.get_user_path('images', '0001.jpg')), c.get_tags()[0]['size'][0])

        db.close_db()
        app.stop()

    def _test_search_tag_category(self, app, *args):
        db = self.init_db_with_categorized_tags()
        c = self.session.cursor

        db.search_tag("cat1:one")
        self.assertEqual(1, len(c))

        db.search_tag("cat1:")
        self.assertEqual(2, len(c))

        db.search_tag("two")
        self.assertEqual(1, len(c))

        db.search_tag("cat1:*", "-one")
        self.assertEqual(1, len(c))
        self.assertEqual("/0003.jpg", c.filename)

        db.search_tag("t", "-letter:")
        self.assertEqual(1, len(c))
        self.assertEqual("/0002.jpg", c.filename)

        db.search_tag("-cat2:", "-cat1:three")
        self.assertEqual(1, len(c))
        self.assertEqual("/0001.jpg", c.filename)

        db.search_tag("o", "cat1:")
        self.assertEqual(1, len(c))
        self.assertEqual("/0001.jpg", c.filename)

        db.search_tag("cat1:three", "cat1:3")
        self.assertEqual(1, len(c))

        db.close_db()
        app.stop()

    def _test_search_tag_numeric(self, app, *args):
        db = self.init_db_with_numeric_date_tags()
        c = self.session.cursor

        # test equals
        db.search_tag("height:81", "width:159")
        self.assertEqual(1, len(c))

        db.search_tag("width:39")
        self.assertEqual(1, len(c))

        # test same kind
        db.search_tag("height:159", "height:81")
        self.assertEqual(0, len(c))

        # test lower than
        db.search_tag("height:<:81")
        self.assertEqual(1, len(c))

        # test multiple lower than with or
        db.search_tag("height:<:81:100")
        self.assertEqual(3, len(c))

        # test multiple lower than with and
        db.search_tag("height:<:81", "height:<:100")
        self.assertEqual(1, len(c))

        # test greater than
        db.search_tag("width:>:40")
        self.assertEqual(2, len(c))

        # test multiple greater than with or
        db.search_tag("width:>:40:100")
        self.assertEqual(2, len(c))

        # test multiple greater than with or
        db.search_tag("width:>:40", "width:>:100")
        self.assertEqual(1, len(c))

        # test lower or equals
        db.search_tag("width:<=:60")
        self.assertEqual(2, len(c))

        # test lower or equals or
        db.search_tag("width:<=:60:40")
        self.assertEqual(2, len(c))

        # test lower or equals or
        db.search_tag("width:<=:60:40:300")
        self.assertEqual(3, len(c))

        # test greater or equals
        db.search_tag("height:>=:81")
        self.assertEqual(2, len(c))

        # test greater or equals or
        db.search_tag("height:>=:81:300")
        self.assertEqual(2, len(c))

        # test greater or equals or
        db.search_tag("height:>=:81:300:20")
        self.assertEqual(3, len(c))

        # test height in 50-70
        db.search_tag("height:><:50:70")
        self.assertEqual(1, len(c))

        # test width in 50-70 or 130-170
        db.search_tag("width:><:50:70:130:170")
        self.assertEqual(2, len(c))

        # test width in 50-70 and 130-170
        db.search_tag("width:><:50:70", "width:><:130:170")
        self.assertEqual(0, len(c))

        db.close_db()
        app.stop()

    def _test_search_tag_dates(self, app, *args):
        db = self.init_db_with_numeric_date_tags()
        c = self.session.cursor

        # test year
        db.search_tag("modification_date:YY:2016")
        self.assertEqual(1, len(c))

        db.search_tag("modification_date:YY:2017")
        self.assertEqual(2, len(c))

        db.search_tag("modification_date:YY:2016:2017")
        self.assertEqual(3, len(c))

        # test month
        db.search_tag("modification_date:YM:201708")
        self.assertEqual(2, len(c))

        db.search_tag("modification_date:YM:201702")
        self.assertEqual(0, len(c))

        # test day
        db.search_tag("modification_date:YMD:20170827")
        self.assertEqual(1, len(c))

        db.search_tag("modification_date:YMD:20170828")
        self.assertEqual(0, len(c))

        db.search_tag("modification_date:YMD:20170827:20160317")
        self.assertEqual(2, len(c))

        # test greater than
        db.search_tag("modification_date:>:%{MKDATE(20170826)}%")
        self.assertEqual(1, len(c))

        # test smaller than
        db.search_tag("modification_date:<:%{MKDATE(20160101)}%")
        self.assertEqual(0, len(c))

        # test add day and today
        db.search_tag("modification_date:><:%{TODAY()}%:%{ADD_DATE(TODAY(),'D',2)}%")
        self.assertEqual(0, len(c))

        # test add month
        db.search_tag("modification_date:%{ADD_DATE(TODAY(),'M',1)}%")
        self.assertEqual(0, len(c))

        # test remove year
        db.search_tag("modification_date:<:%{ADD_DATE(TODAY(),'Y',-13)}%")
        self.assertEqual(0, len(c))
        db.search_tag("modification_date:>:%{ADD_DATE(TODAY(),'Y',-13)}%")
        self.assertEqual(3, len(c))

        # test combination
        db.search_tag("modification_date:YY:%{TO_Y(ADD_DATE(MKDATE(20170827),'Y',-1))}%")
        self.assertEqual(1, len(c))

        db.search_tag("modification_date:YY:%{TO_Y(MKDATE(20170827))-1}%")
        self.assertEqual(1, len(c))

        db.search_tag("modification_date:YM:%{TO_YM(MKDATE(20170827))}%")
        self.assertEqual(2, len(c))

        db.close_db()
        app.stop()

    def _test_search_core_tags(self, app, *args):
        db = self.init_db()
        c = self.session.cursor

        # test extension
        db.search_tag("ext:jpg")
        self.assertEqual(3, len(c))

        db.search_tag("ext:in:gif:png")
        self.assertEqual(0, len(c))

        db.search_tag("ext:in:jpg:png")
        self.assertEqual(3, len(c))

        # search for date
        db.search_tag("file_date:YY:2017")
        self.assertEqual(3, len(c))

        db.search_tag("file_date:YM:201709")
        self.assertEqual(1, len(c))

        db.search_tag("file_date:YM:201708")
        self.assertEqual(0, len(c))

        db.search_tag("file_date:YM:201704")
        self.assertEqual(2, len(c))

        # search for both extension and date
        db.search_tag("ext:jpg", "file_date:YY:2017")
        self.assertEqual(3, len(c))

        db.search_tag("ext:jpg", "file_date:YY:2016")
        self.assertEqual(0, len(c))

        # search with negation
        db.search_tag("ext:jpg", "file_date:YY:2017", "-file_date:YM:201709")
        self.assertEqual(2, len(c))

        db.search_tag("ext:jpg", "file_date:YY:2017", "-file_date:YM:201709", "-size:<:1000")
        self.assertEqual(1, len(c))

        db.search_tag("width:39")
        self.assertEqual(3, len(c))

        db.search_tag("width:<:40")
        self.assertEqual(3, len(c))

        # mix core tags and custom tags
        db.search_tag()
        c = self.session.cursor

        c.add_tag("one")

        db.search_tag("file_date:YM:201704", "*:in:one:toto")
        self.assertEqual(1, len(c))

        db.close_db()
        app.stop()

    def _test_search_partial_text(self, app, *args):
        db = self.init_db_with_tags()
        c = self.session.cursor

        db.search_tag("geno%")
        self.assertEqual(1, len(c))

        db.search_tag("ada%")
        self.assertEqual(2, len(c))

        db.search_tag("%eno%")
        self.assertEqual(2, len(c))

        db.search_tag("*:%:%bla%", "%e")
        self.assertEqual(1, len(c))

        db.search_tag("%ada%", "-%bla%")
        self.assertEqual(1, len(c))

        db.search_tag("*:%:%ada%:%bla%")
        self.assertEqual(3, len(c))

        db.close_db()
        app.stop()

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def test_initialization(self):
        self.call_test(self._test_initialization)

    def test_search_all(self):
        self.call_test(self._test_search_all)

    def test_search_tag(self):
        self.call_test(self._test_search_tag)

    def test_update_file(self):
        self.call_test(self._test_update_file)

    def test_update_tags(self):
        self.call_test(self._test_update_tags)

    def test_search_tag_category(self):
        self.call_test(self._test_search_tag_category)

    def test_search_tag_numeric(self):
        self.call_test(self._test_search_tag_numeric)

    def test_search_tag_dates(self):
        self.call_test(self._test_search_tag_dates)

    def test_search_partial_text(self):
        self.call_test(self._test_search_partial_text)

    def test_search_core_tags(self):
        self.call_test(self._test_search_core_tags)


if __name__ == "__main__":
    unittest.main()
