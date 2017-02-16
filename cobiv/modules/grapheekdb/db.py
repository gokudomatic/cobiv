import grapheekdb
from grapheekdb.backends.data.symaslmdb import LmdbGraph
import os
from os import listdir
from os.path import isfile, join
from PIL import Image
from kivy.app import App

from cobiv.common import set_action
from cobiv.modules.imageset.ImageSet import current_imageset

NODE_TYPE_CATALOGUE = "catalogue"
NODE_TYPE_REPOSITORY = "repository"
NODE_TYPE_FILE = "file"
NODE_TYPE_TAG = "tag"

TAG_TYPE_TAG = "tag"

SUPPORTED_IMAGE_FORMATS = ["jpg", "gif", "png"]


class Database:
    def __init__(self):
        self.g = LmdbGraph("db")
        if self.g.V().count() == 0:
            self.init_database()

        # add actions
        set_action("search",self.search_tag,"viewer")
        set_action("add-tag",self.add_tag,"viewer")
        set_action("rm-tag",self.remove_tag,"viewer")

    def init_database(self):
        cat=self.create_catalogue("default")
        self.add_repository(cat,"C:\\Users\\edwin\\Pictures")

    def create_catalogue(self, name):
        return self.g.add_node(name=name, kind=NODE_TYPE_CATALOGUE)

    def add_repository(self, catalogue, path, recursive=True):
        if catalogue.outE(kind="own").outV(path=path).count() > 0:
            repo_node = catalogue.outE(kind="own").outV(path=path)[0]
        else:
            name = path.split(os.sep)[-1]
            if len(name) == 0:
                name = path

            repo_node = self.g.add_node(name=name, path=path, kind=NODE_TYPE_REPOSITORY, recursive=recursive)
            self.g.add_edge(catalogue, repo_node, kind="own")
        self.update_dir(repo_node, path, recursive)

    def update_dir(self, repo, path, recursive):

        if recursive:
            result = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
                      os.path.splitext(f)[1][1:] in SUPPORTED_IMAGE_FORMATS]
        else:
            result = [join(path, f) for f in listdir(path) if
                      isfile(join(path, f)) and f.split('.')[-1] in SUPPORTED_IMAGE_FORMATS]

        existing = [n.name for n in repo.out_(kind="own")]

        new_files = list(set(result) - set(existing))
        removed_files = list(set(existing) - set(result))

        # add new ones
        for f in new_files:
            node = self.g.add_node(name=f, kind=NODE_TYPE_FILE, path=os.path.dirname(f),
                                   filename=os.path.basename(f), ext=os.path.splitext(f)[1][1:])
            self.g.add_edge(repo, node, kind="own")
            self.read_tags(node)

        # remove old ones
        for f in removed_files:
            repo.outE(kind="own").outV(kind=NODE_TYPE_FILE, name=f).remove()

    def read_tags(self, node):
        img = Image.open(node.name)
        if img.info:
            for i, v in img.info.iteritems():
                if i == "tags":
                    tag_list=v.split(",")
                    for tag in tag_list:
                        tag_node=self._create_tag(tag.strip())
                        self.g.add_edge(node, tag_node, kind="has")

    def _create_tag(self,value):
        tn = self.g.V(kind=NODE_TYPE_TAG, type=TAG_TYPE_TAG, value=value)
        if tn.count() > 0:
            return tn[0]
        else:
            return self.g.add_node(kind=NODE_TYPE_TAG, type=TAG_TYPE_TAG, value=value)

    def search_tag(self,*args):
        print current_imageset
        root=App.get_running_app().root
        current_imageset.uris=[n.name for n in self.g.V(kind=NODE_TYPE_FILE)]
        root.execute_cmd("load-set")

    def add_tag(self,*args):
        print("idx = "+str(current_imageset.current))

    def remove_tag(self,*args):
        pass

db = Database()
