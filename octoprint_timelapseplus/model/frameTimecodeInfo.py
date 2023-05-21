import datetime

from ..helpers.timeHelper import TimeHelper


class FrameTimecodeInfo:
    def __init__(self, timestamp, started, ended):
        self.TIMESTAMP = timestamp
        self.STARTED = started
        self.ENDED = ended

    def getElapsedSeconds(self):
        return self.TIMESTAMP - self.STARTED

    def getRatio(self):
        span = self.ENDED - self.STARTED
        return self.getElapsedSeconds() / span

    def getDateTime(self):
        return datetime.datetime.fromtimestamp(self.TIMESTAMP)

    @staticmethod
    def getDummy():
        seconds1Hour = 60 * 60
        now = TimeHelper.getUnixTimestamp()
        started = now - seconds1Hour
        ended = now + seconds1Hour
        return FrameTimecodeInfo(now, started, ended)
