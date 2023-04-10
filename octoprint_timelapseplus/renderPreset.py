class RenderPreset:
   def __init__(self):
      self.FRAMERATE = 30
      self.INTERPOLATE = False
      self.INTERPOLATE_FRAMERATE = 60
      self.INTERPOLATE_MODE = 'mci'  # 'blend'
      self.INTERPOLATE_ESTIMATION = 'bidir'
      self.INTERPOLATE_COMPENSATION = 'aobmc'