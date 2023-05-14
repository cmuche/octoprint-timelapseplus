import time


class TimeHelper:
    @staticmethod
    def getUnixTimestamp():
        return int(time.time())