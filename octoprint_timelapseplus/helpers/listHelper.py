class ListHelper:

    @staticmethod
    def chunkList(inputList, chunkSize):
        return [inputList[i:i + chunkSize] for i in range(0, len(inputList), chunkSize)]

    def rangeList(n):
        return [i for i in range(1, n + 1)]
