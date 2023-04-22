import os


class Mask:
    def __init__(self, parent, dataFolder, id) -> None:
        if id is None:
            self.ID = parent.getRandomString(32)
        else:
            self.ID = id

        folder = self.getMaskFolder(dataFolder)
        self.PATH = folder + '/' + self.ID + '.png'
        os.makedirs(folder, exist_ok=True)

    @staticmethod
    def getMaskFolder(dataFolder):
        return dataFolder + '/mask'
