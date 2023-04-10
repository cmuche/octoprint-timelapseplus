import hashlib
import os


class Video:
    def __init__(self, path, parent, logger):
        self.PARENT = parent
        self._logger = logger

        self.FILE = os.path.splitext(os.path.basename(path))[0]
        self.THUMBNAIL = path + '.thumb.jpg'
        self.PATH = path
        self.TIMESTAMP = os.path.getmtime(path)
        self.SIZE = os.path.getsize(path)

        self.HASH = self.getHash()
        self.ID = self.getId()

    def delete(self):
        os.remove(self.PATH)
        if os.path.exists(self.THUMBNAIL):
            os.remove(self.THUMBNAIL)

    def getJSON(self):
        return dict(
            id=self.ID,
            file=self.FILE,
            size=self.SIZE,
            timestamp=self.TIMESTAMP,
            thumbnail='/api/plugin/octoprint_timelapseplus?command=thumbnail&type=video&id=' + self.ID
        )

    def getId(self):
        c = self.HASH + self.PATH + str(self.TIMESTAMP)
        return hashlib.md5(c.encode('utf-8')).hexdigest()

    def getHash(self):
        with open(self.PATH, "rb") as f:
            firstBytes = f.read(256)
        return hashlib.md5(firstBytes).hexdigest()
