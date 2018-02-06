import os

import sys
from kivy.uix.image import Image


class BookBrowserThumbnail(Image):
    file_exists = False

    def __init__(self, source=None, **kwargs):
        source=os.path.join(os.path.dirname(sys.argv[0]), "resources", "icons", "book.png")
        super().__init__(source=source, **kwargs)
