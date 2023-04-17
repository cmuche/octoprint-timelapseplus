import glob
import hashlib
import os
import json


class CacheController:
    def __init__(self, parent, dataFolder, settings):
        self.PARENT = parent
        self._data_folder = dataFolder
        self._settings = settings

        self.DIR = dataFolder + '/cache'
        self.prepareFolder()

    def prepareFolder(self):
        os.makedirs(self.DIR, exist_ok=True)
        files = glob.glob(self.DIR + '/*')
        for f in files:
            os.remove(f)

    def getIdHash(self, idList):
        jsonStr = json.dumps(idList)
        jsonEnc = jsonStr.encode('utf-8')
        return hashlib.md5(jsonEnc).hexdigest()

    def getIdFile(self, idList):
        hash = self.getIdHash(idList)
        path = self.DIR + '/' + hash + '.cache'
        return path

    def isCached(self, idList):
        file = self.getIdFile(idList)
        return os.path.exists(file)

    def getBytes(self, idList):
        file = self.getIdFile(idList)
        with open(file, 'rb') as f:
            return f.read()

    def storeBytes(self, idList, bytes):
        file = self.getIdFile(idList)
        with open(file, 'wb') as f:
            f.write(bytes)

    def getString(self, idList):
        file = self.getIdFile(idList)
        with open(file, 'r') as f:
            return f.read()

    def storeString(self, idList, str):
        file = self.getIdFile(idList)
        with open(file, 'w') as f:
            f.write(str)
