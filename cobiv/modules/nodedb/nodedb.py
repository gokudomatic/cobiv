import sys
import os
from os import listdir
from os.path import isfile, join
from PIL import Image
from kivy.app import App
from kivy.factory import Factory
from kivy.properties import NumericProperty

from cobiv.common import set_action
from cobiv.modules.component import Component
from cobiv.modules.entity import Entity

import threading
from blitzdb import FileBackend, Document

from cobiv.modules.session.cursor import Cursor

SUPPORTED_IMAGE_FORMATS = ["jpg", "gif", "png"]


class Catalog(Document):
    pass


class Repository(Document):
    pass


class File(Document):
    pass


class Slide(Document):
    pass


class BlitzCursor(Cursor):
    slide = None
    db = None

    def __init__(self, slide,backend=None):
        self.slide = slide
        self.db=backend

    def get_next(self):
        return BlitzCursor(self.slide.next,self.db) if self.slide is not None else self

    def get_previous(self):
        return BlitzCursor(self.slide.previous,self.db) if self.slide is not None else self

    def get_tags(self):
        return []

    def filename(self):
        print self.slide.filename
        return self.slide.filename if self.slide is not None else None

    def get_first(self):
        if self.slide is None:
            return self

        try:
            return BlitzCursor(self.db.get(Slide,{'set':self.slide.set,'index':0}),self.db)
        except Slide.DoesNotExist:
            return self

    def get_last(self):
        if self.slide is None:
            return self

        try:
            return BlitzCursor(self.db.get(Slide,{'set':self.slide.set,'next':None}),self.db)
        except Slide.DoesNotExist:
            return self

    def get(self, idx):
        if self.slide is None:
            return self

        try:
            return BlitzCursor(self.db.get(Slide,{'set':self.slide.set,'index':idx}),self.db)
        except Slide.DoesNotExist:
            return self

    def __len__(self):
        return 0 if self.slide is None else len(self.db.filter(Slide,{'set':self.slide.set}))

class NodeDb(Entity):
    # current_imageset = None
    thread_max_files = 0
    thread_count = 0
    cancel_operation = False
    session = None

    def __init__(self):
        self.g = FileBackend("db.cache")

        # add actions
        set_action("search", self.search_tag, "viewer")
        set_action("search", self.search_tag, "browser")
        set_action("add-tag", self.add_tag, "viewer")
        set_action("rem-tag", self.remove_tag, "viewer")
        set_action("ls-tag", self.list_tags, "viewer")
        set_action("updatedb", self.updatedb)
        set_action("t1", self.test1)
        set_action("t2", self.test2)

    def init_database(self):
        self.g.register(Catalog)
        self.g.register(Repository)
        self.g.register(File)
        cat = self.create_catalogue("default")
        self.add_repository(cat, "C:\\Users\\edwin\\Pictures")
        self.updatedb()
        self.g.create_index(File, fields={'name': 1})
        self.g.create_index(File, fields={'tags': 1})
        self.g.create_index(Slide, fields={'set': 1})
        self.g.create_index(Slide, fields={'index': 1})

    def ready(self):
        Component.ready(self)
        self.session = self.get_app().lookup("session", "Entity")
        # self.current_imageset = self.session.get_currentset()
        try:
            cat = self.g.get(Catalog, {'name': 'default'})
        except Catalog.DoesNotExist:
            self.init_database()

    def create_catalogue(self, name):
        cat = Catalog({
            'name': name,
            'repositories': []
        })
        self.g.save(cat)
        self.g.commit()

        return cat

    def add_repository(self, catalogue, path, recursive=True):
        if not path in [repo.path for repo in catalogue.repositories]:
            name = path.split(os.sep)[-1]
            if len(name) == 0:
                name = path

            repo_node = Repository({
                'name': name,
                'path': path,
                'recursive': recursive,
                'catalogue': catalogue,
                'files': []
            })

            catalogue.repositories.append(repo_node)

            self.g.save(catalogue)
            self.g.commit()

    def updatedb(self):
        threading.Thread(target=self._threaded_updatedb).start()

    def _threaded_updatedb(self):
        self.start_progress("Initializing update...")
        repos = self.g.filter(Repository, {})

        differences = []

        self.thread_max_files = 0
        for repo in repos:
            to_add, to_remove = self._update_get_diff(repo)
            differences.append((repo, to_add, to_remove))
            self.thread_max_files += len(to_add) + len(to_remove)

        self.thread_count = 0

        for diff in differences:
            self._update_dir(diff[0], diff[1], diff[2])
            if self.cancel_operation:
                break

        self.set_progress(0, "Creating default set...")

        self.regenerate_set('*', self.g.filter(File, {}), caption="Indexing file {} of {}")

        self.stop_progress()

    def regenerate_set(self, set_name, resultset, caption=None):
        self.g.filter(Slide, {'set': set_name}).delete()
        prev = None
        self.thread_max_files = len(resultset)
        self.thread_count = 0
        for file in resultset:
            prev = self.add_slide(set_name, self.thread_count, file.name, prev)
            self.thread_count += 1
            if caption != None:
                self.set_progress(self.thread_count * 100 / self.thread_max_files,
                                  caption=caption.format(self.thread_count, self.thread_max_files))

        self.g.commit()

    def _update_get_diff(self, repo):
        path = repo.path
        recursive = repo.recursive
        if recursive:
            result = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
                      os.path.splitext(f)[1][1:] in SUPPORTED_IMAGE_FORMATS]
        else:
            result = [join(path, f) for f in listdir(path) if
                      isfile(join(path, f)) and f.split('.')[-1] in SUPPORTED_IMAGE_FORMATS]

        existing = [n.name for n in self.g.filter(File, {'repository.pk': repo.pk})]

        new_files = set(result) - set(existing)
        removed_files = set(existing) - set(result)
        return new_files, removed_files

    def _update_dir(self, repo, to_add, to_rem):
        # add new ones
        for f in to_add:
            if self.cancel_operation:
                return
            self.set_progress(self.thread_count * 100 / self.thread_max_files,
                              caption="Importing file {} of {}".format(self.thread_count, self.thread_max_files))

            node = File(attributes={
                'name': f,
                'path': os.path.dirname(f),
                'filename': os.path.basename(f),
                'ext': os.path.splitext(f)[1][1:],
                'repository': repo,
                'tags': []
            })
            repo.files.append(node)
            self.read_tags(node)
            self.g.save(node)
            self.thread_count += 1

        self.g.commit()

        # remove old ones
        for f in to_rem:
            if self.cancel_operation:
                return
            self.set_progress(self.thread_count * 100 / self.thread_max_files,
                              caption="Deleting file {} of {}".format(self.thread_count, self.thread_max_files))

            self.g.delete(self.g.get(File, {'name': f}))

            self.thread_count += 1

        self.g.commit()

    def read_tags(self, node):
        img = Image.open(node.name)
        if img.info:
            for i, v in img.info.iteritems():
                if i == "tags":
                    tag_list = v.split(",")
                    for tag in tag_list:
                        node.tags.append(tag.strip())

    def copy_set_to_current(self,set_name):
        self.g.filter(Slide, {'set': 'current'}).delete()

        prev=None
        for slide in self.g.filter(Slide,{'set':set_name}):
            prev=self.add_slide('current',slide.index,slide.filename,prev)

        self.g.commit()

    def search_tag(self, *args):
        root = self.get_app().root

        if len(args) == 0:
            self.copy_set_to_current('*')

        else:
            to_include = []
            to_exclude = []

            for arg in args:
                if arg[0] == "-":
                    to_exclude.append(arg[1:])
                else:
                    to_include.append(arg)

            query = []
            if len(to_include) > 0:
                query.append({'tags': {'$all': to_include}})
            query.append({'tags': {'$not': {'$in': to_exclude}}})

            resultset = self.g.filter(File, {'$and': query})

            self.regenerate_set('current', resultset)

        try:
            self.session.cursor = BlitzCursor(self.g.get(Slide, {'set': 'current', 'index': 0}),self.g)
        except Slide.DoesNotExist:
            self.session.cursor = Cursor(None)

        # filenames = [n.name for n in resultset]

        # self.current_imageset.uris = filenames

        root.execute_cmd("load-set")

    def add_tag(self, *args):
        n = self.g.get(File, {'name': self.session.get_current_image()})
        for tag in args:
            try:
                n.tags.append(tag)
            except:
                pass
        self.g.save(n)
        self.g.commit()

    def remove_tag(self, *args):
        n = self.g.get(File, {'name': self.session.get_current_image()})
        for tag in args:
            try:
                n.tags.remove(tag)
            except:
                pass
        self.g.save(n)
        self.g.commit()

    def list_tags(self):
        n = self.g.get(File, {'name': self.session.get_current_image()})
        for tag in n.tags:
            App.get_running_app().root.notify(tag.value)

    def on_application_quit(self):
        self.cancel_operation = True

    def add_slide(self, set, idx, filename, previous):
        slide = Slide({'set': set, 'index': idx, 'filename': filename, 'previous': previous, 'next': None})
        slide = self.g.save(slide)
        if previous != None:
            previous.next = slide
            self.g.update(previous, ('next',))
        return slide

    def test1(self):
        fs = self.g.filter(File, {'$and': [{'tags': {'$all': ['anal']}}, {'tags': {'$not': {'$in': ['sdfsd']}}}]})
        print len(fs)

    def test2(self):
        fs = self.g.get(File, {'name': 'C:\\Users\\edwin\Pictures\\-Artist- RandomRandom\\157_Gwen_8a.png'})
        fs.tags.append('gwen')
        self.g.save(fs)
        self.g.commit()


Factory.register('Cursor', module=BlitzCursor)
