import hashlib

from cobiv.modules.reader.tagreader import TagReader


class TagCrcReader(TagReader):

    hasher = hashlib.md5()

    def read_file_tags(self,file_id,filename,list_to_add):

        with open(filename, 'rb') as afile:
            buf = afile.read()
            self.hasher.update(buf)
        list_to_add.append((file_id, 0, 'crc', self.hasher.hexdigest()))