from PIL import Image


class PPRollRenderer:
    @staticmethod
    def renderFrame(ratio, frames, preset):
        img = Image.new("RGBA", (1920, 1080))

        retFrameIdx = int(round((1 - ratio) * len(frames) - 1))
        fImg = Image.open(frames[retFrameIdx])
        img.paste(fImg, (0, 0))

        return img.convert('RGB')
