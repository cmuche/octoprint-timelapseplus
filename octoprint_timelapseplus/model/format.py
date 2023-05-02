class Format:
    def __init__(self, id, name, title, extension, mimeType, codecName, codecId, additionalArgs=dict()):
        self.ID = id
        self.NAME = name
        self.TITLE = title
        self.EXTENSION = extension
        self.MIME_TYPE = mimeType
        self.CODEC_NAME = codecName
        self.CODEC_ID = codecId
        self.ADDITIONAL_ARGS = additionalArgs

    def getJSON(self):
        return dict(
            id=ID,
            name=self.NAME,
            title=self.TITLE,
            extension=self.EXTENSION,
            mimeType=self.MIME_TYPE,
            codecName=self.CODEC_NAME
        )

    def getFullName(self):
        ret = self.NAME
        if self.CODEC_NAME is not None:
            ret += '(' + self.CODEC_NAME + ')'
        return ret

    def getRenderArgs(self):
        ret = []

        if self.CODEC_ID is not None:
            ret += ['-c:v', self.CODEC_ID]

        for k in self.ADDITIONAL_ARGS.keys():
            v = str(self.ADDITIONAL_ARGS[k])
            ret += [k, v]

        return ret
