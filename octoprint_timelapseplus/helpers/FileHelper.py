import os


class FileHelper:

    @staticmethod
    def getUniqueFileName(filePath):
        if not os.path.isfile(filePath):
            return filePath

        fileDir, fileName = os.path.split(filePath)
        name, extension = os.path.splitext(fileName)

        suffix = 1
        newName = f"{name}-{suffix}{extension}"
        newPath = os.path.join(fileDir, newName)
        while os.path.isfile(newPath):
            suffix += 1
            newName = f"{name}-{suffix}{extension}"
            newPath = os.path.join(fileDir, newName)

        return newPath
