import os
import unittest
from functools import partial
from time import sleep

from fs import open_fs
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

from cobiv.modules.core.session.Session import Session
from cobiv.modules.core.thumbloader.thumbloader import ThumbLoader


class TestMainWidget(Widget):
    def execute_cmd(self, *args, **kwargs):
        pass

    def execute_cmds(self, *args, **kwargs):
        pass

    def show_progressbar(self, *args, **kwargs):
        pass

    def set_progressbar_value(self, *args, **kwargs):
        pass

    def close_progressbar(self, *args, **kwargs):
        pass


class TestApp(App):
    session = None

    def __init__(self, **kwargs):
        super(TestApp, self).__init__(**kwargs)
        self.configuration = {
            'thumbloader.path': self.get_user_path('thumbs'),
            'thumbloader.image_size': 120
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

    def register_event_observer(self, name, fallback):
        pass

    def lookup(self, object_name, category):
        if category == "Entity" and object_name == "session":
            return self.session
        else:
            return []


class ThumbloaderTest(unittest.TestCase):
    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    def setUp(self):
        self.session = Session()
        self.session.add_filesystem(1, open_fs(u'osfs://images'))

    def tearDown(self):
        super(ThumbloaderTest, self).tearDown()
        path = self.get_user_path('thumbs')
        [os.remove(os.path.join(path, f)) for f in os.listdir(path)]

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def get_thumbloader(self, app):
        app.session = self.session
        t = ThumbLoader()
        t.ready()
        t.restart()
        return t

    def _test_initialization(self, app, *args):
        t = self.get_thumbloader(app)

        t.stop()
        app.stop()

    def wait_for(self, t, size):
        for i in range(5 * size + 1):
            if t.queue_empty:
                break
            sleep(0.2)
        self.assertTrue(t.queue_empty)

    def _test_enqueue_images(self, app, *args):
        t = self.get_thumbloader(app)

        self.assertEqual(0, len(t.to_cache))

        t.append((1, u'/0001.jpg', 1))
        self.assertEqual(1, len(t.to_cache))
        self.wait_for(t, 1)
        self.assertEqual(0, len(t.to_cache))
        self.assertEqual(1, len(os.listdir(self.get_user_path('thumbs'))))

        t.append((1, u'/0001.jpg', 1), (2, u'/0002.jpg', 1),
                 (3, u'/0003.jpg', 1))
        self.assertEqual(3, len(t.to_cache))
        self.wait_for(t, 3)
        self.assertEqual(0, len(t.to_cache))
        self.assertEqual(3, len(os.listdir(self.get_user_path('thumbs'))))

        t.append((2, u'/0002.jpg', 1))
        self.assertEqual(1, len(t.to_cache))
        self.wait_for(t, 1)
        self.assertEqual(0, len(t.to_cache))
        self.assertEqual(3, len(os.listdir(self.get_user_path('thumbs'))))

        t.stop()
        app.stop()

    def _test_remove_images(self, app, *args):
        t = self.get_thumbloader(app)

        t.append((1, u'/0001.jpg', 1))
        self.wait_for(t, 1)
        self.assertEqual(1, len(os.listdir(self.get_user_path('thumbs'))))

        t.delete_thumbnail(1)
        self.assertEqual(0, len(os.listdir(self.get_user_path('thumbs'))))

        t.append((1, u'/0001.jpg', 1), (2, u'/0002.jpg', 1),
                 (3, u'/0003.jpg', 1))
        self.wait_for(t, 3)
        t.delete_thumbnail(2)
        self.assertEqual(2, len(os.listdir(self.get_user_path('thumbs'))))
        t.delete_thumbnail(1, 2)
        self.assertEqual(1, len(os.listdir(self.get_user_path('thumbs'))))

        t.stop()
        app.stop()

    def test_initialization(self):
        self.call_test(self._test_initialization)

    def test_enqueue_images(self):
        self.call_test(self._test_enqueue_images)

    def test_remove_images(self):
        self.call_test(self._test_remove_images)


if __name__ == "__main__":
    unittest.main()
