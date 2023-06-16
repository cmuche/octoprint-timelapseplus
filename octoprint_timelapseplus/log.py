class Log:
    def __init__(self):
        self.LOGGER = None

    @staticmethod
    def genMsg(msg, payload):
        msg = str(msg)

        if payload is not None:
            try:
                msg += ' - ' + str(payload)
            except:
                pass

        return msg

    @staticmethod
    def debug(msg, payload=None):
        if Log.LOGGER is None:
            return

        Log.LOGGER.debug(Log.genMsg(msg, payload))

    @staticmethod
    def info(msg, payload=None):
        if Log.LOGGER is None:
            return

        Log.LOGGER.info(Log.genMsg(msg, payload))

    @staticmethod
    def warning(msg, payload=None):
        if Log.LOGGER is None:
            return

        Log.LOGGER.warning(Log.genMsg(msg, payload))

    @staticmethod
    def error(msg, payload=None):
        if Log.LOGGER is None:
            return

        Log.LOGGER.error(Log.genMsg(msg, payload))

    @staticmethod
    def critical(msg, payload=None):
        if Log.LOGGER is None:
            return

        Log.LOGGER.critical(Log.genMsg(msg, payload))
