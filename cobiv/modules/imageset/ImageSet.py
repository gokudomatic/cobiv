from kivy.uix.image import AsyncImage


class ImageSet:
    uris = []

    def images(self):
        for uri in self.uris:
            yield AsyncImage(source=uri, allow_stretch=True)


current_imageset = ImageSet()
