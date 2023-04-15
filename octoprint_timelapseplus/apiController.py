import base64
import glob
import io
import os
import random
import re
import string
from threading import Thread
from time import sleep

from PIL import Image
from flask import make_response, send_file

from .model.mask import Mask


class ApiController:
    def __init__(self, parent, dataFolder, settings):
        self.PARENT = parent
        self._data_folder = dataFolder
        self._settings = settings

    def createBlurMask(self):
        import flask
        imgBase64 = flask.request.get_json()['image']
        imgData = base64.b64decode(re.sub('^data:image/.+;base64,', '', imgBase64))
        image = Image.open(io.BytesIO(imgData)).convert('L')

        mask = Mask(self.PARENT, self._data_folder, None)
        image.save(mask.PATH)

        return dict(id=mask.ID)
