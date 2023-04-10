import hashlib
import os
import zipfile
from contextlib import closing
from zipfile import ZipFile


class FrameZip:
    def __init__(self, path, parent, logger):
        self.PARENT = parent
        self._logger = logger

        self.FILE = os.path.splitext(os.path.basename(path))[0]
        self.PATH = path
        self.FRAMES = self.countFrames()
        self.TIMESTAMP = os.path.getmtime(path)
        self.SIZE = os.path.getsize(path)

        self.HASH = self.getHash()
        self.ID = self.getId()

    def delete(self):
        os.remove(self.PATH)

    def getThumbnail(self):
        zip = zipfile.ZipFile(self.PATH, 'r')
        nl = zip.namelist()
        img = zip.read(nl[-1])
        return img

    def getId(self):
        c = self.HASH + self.PATH + str(self.TIMESTAMP)
        return hashlib.md5(c.encode('utf-8')).hexdigest()

    def getJSON(self):
        return dict(
            id=self.ID,
            file=self.FILE,
            frames=self.FRAMES,
            size=self.SIZE,
            timestamp=self.TIMESTAMP,
            thumbnail='/api/plugin/octoprint_timelapseplus?command=thumbnail&type=frameZip&id=' + self.ID
        )

    def getHash(self):
        with open(self.PATH, "rb") as f:
            firstBytes = f.read(256)
        return hashlib.md5(firstBytes).hexdigest()

    def countFrames(self):
        with closing(ZipFile(self.PATH)) as archive:
            count = len(archive.infolist())
        return count
