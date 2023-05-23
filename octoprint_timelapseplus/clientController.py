import copy

from deepdiff import DeepDiff

from octoprint.util import ResettableTimer


class ClientController:

    def __init__(self, parent, identifier, pluginManager):
        self.PARENT = parent
        self._identifier = identifier
        self._pluginManager = pluginManager
        self.QUEUE = dict()
        self.LAST_DATA = dict()
        self.INTERVAL = 250
        self.TIMER = None
        self.TIMER_ACTIVE = False

    def sendData(self, data):
        for k in data:
            self.LAST_DATA[k] = data[k]

        sd = copy.deepcopy(data)
        sd['type'] = 'data'
        self._pluginManager.send_plugin_message(self._identifier, sd)

    def sendQueue(self):
        #print(self.QUEUE.keys())

        if not self.TIMER_ACTIVE:
            self.startTimer()
            self.sendData(self.QUEUE)
            self.QUEUE = dict()

    def startTimer(self):
        if self.TIMER is not None:
            self.TIMER.cancel()

        self.TIMER = ResettableTimer(float(self.INTERVAL) / 1000.0, self.timerTriggered)
        self.TIMER.start()
        self.TIMER_ACTIVE = True

    def timerTriggered(self):
        self.TIMER.cancel()
        self.TIMER_ACTIVE = False

        if not self.dictsAreEqual(dict(), self.QUEUE):
            self.sendQueue()

    def dictsAreEqual(self, d1, d2):
        dd = DeepDiff(d1, d2, ignore_order=True)
        return not bool(dd)

    def enqueueData(self, data, force):
        if force:
            self.sendData(data)
            return

        for k in data:
            v = data[k]
            if not (k in self.LAST_DATA and self.dictsAreEqual(self.LAST_DATA[k], v)):
                self.QUEUE[k] = v

        self.sendQueue()
