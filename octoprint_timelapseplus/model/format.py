class Format:
    def __init__(self, id, name, title, extension, mimeType, codecName, codecId, additionalArgs=dict(), createPalette=False):
        self.ID = id
        self.NAME = name
        self.TITLE = title
        self.EXTENSION = extension
        self.MIME_TYPE = mimeType
        self.CODEC_NAME = codecName
        self.CODEC_ID = codecId
        self.ADDITIONAL_ARGS = additionalArgs
        self.CREATE_PALETTE = createPalette

    def getJSON(self):
        return dict(
            id=self.ID,
            name=self.NAME,
            title=self.TITLE,
            fullName=self.getFullName(),
            extension=self.EXTENSION,
            mimeType=self.MIME_TYPE,
            codecName=self.CODEC_NAME
        )

    def getFullName(self):
        ret = self.NAME

        if self.TITLE is not None:
            ret += ' - ' + self.TITLE

        if self.CODEC_NAME is not None:
            ret += ' (' + self.CODEC_NAME + ')'

        return ret

    def getCodecIdsList(self):
        if self.CODEC_ID is None:
            return []

        if isinstance(self.CODEC_ID, str):
            return [self.CODEC_ID]

        return self.CODEC_ID

    def getRenderArgs(self):
        ret = []

        for k in self.ADDITIONAL_ARGS.keys():
            v = str(self.ADDITIONAL_ARGS[k])
            ret += [k, v]

        if self.CODEC_ID is not None:
            codecId = self.getCodecIdsList()[0]
            ret += ['-c:v', codecId]

        return ret
