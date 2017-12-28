import hashlib

from cobiv.modules.io.reader.tagreader import TagReader


class TagCrcReader(TagReader):
    hasher = hashlib.md5()

    def read_file_tags(self, file_id, data, list_to_add):
        self.hasher.update(data)
        list_to_add.append((file_id, 0, 'crc', 0, self.hasher.hexdigest()))
