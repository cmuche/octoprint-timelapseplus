import re


class ListHelper:

    @staticmethod
    def chunkList(inputList, chunkSize):
        return [inputList[i:i + chunkSize] for i in range(0, len(inputList), chunkSize)]

    @staticmethod
    def rangeList(n):
        return [i for i in range(1, n + 1)]

    @staticmethod
    def extractFileposFromGcodeTag(tags):
        try:
            pattern = r'filepos:(\d+)'
            filepos = None

            for entry in tags:
                match = re.search(pattern, entry)
                if match:
                    filepos = int(match.group(1))
                    break

            return filepos
        except:
            return None
