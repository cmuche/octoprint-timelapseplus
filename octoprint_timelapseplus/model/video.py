import hashlib
import os


class Video:
    def __init__(self, path, parent, logger, settings):
        self.PARENT = parent
        self.CACHE_CONTROLLER = parent.CACHE_CONTROLLER
        self._logger = logger
        self._settings = settings

        self.FILE = os.path.splitext(os.path.basename(path))[0]
        self.THUMBNAIL = path + '.thumb.jpg'
        self.PATH = path
        self.TIMESTAMP = os.path.getmtime(path)
        self.SIZE = os.path.getsize(path)
        self.MIMETYPE = 'video/mp4'
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
            thumbnail='/plugin/octoprint_timelapseplus/thumbnail?type=video&id=' + self.ID,
            url='/plugin/octoprint_timelapseplus/download?type=video&id=' + self.ID
        )

    def getId(self):
        c = self.PATH + str(self.TIMESTAMP) + str(self.SIZE)
        return hashlib.md5(c.encode('utf-8')).hexdigest()
