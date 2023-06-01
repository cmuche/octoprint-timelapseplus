from PIL import Image

from ..model.combineMethod import CombineMethod


class ImageCombineHelper:
    @staticmethod
    def createCombinedImage(imagePaths, method):
        if len(imagePaths) == 1:
            return Image.open(imagePaths[0])

        if method == CombineMethod.DROP:
            return ImageCombineHelper.createDrop(imagePaths)
        if method == CombineMethod.BLEND:
            return ImageCombineHelper.createBlend(imagePaths)
        if method == CombineMethod.BLEND_WEIGHTED:
            return ImageCombineHelper.createBlendWeighted(imagePaths)

    @staticmethod
    def createDrop(imgList):
        return Image.open(imgList[-1])

    @staticmethod
    def createBlend(imagePaths):
        images = []
        for path in imagePaths:
            with Image.open(path) as image:
                images.append(image.convert('RGBA'))

        width, height = images[0].size
        blendedImage = Image.new('RGBA', (width, height), (0, 0, 0))
        for image in images:
            blendedImage = Image.blend(blendedImage, image, 1 / len(images))

        for i in images:
            i.close()

        return blendedImage.convert('RGB')

    @staticmethod
    def createBlendWeighted(imagePaths):
        images = []
        for path in imagePaths:
            with Image.open(path).convert('RGBA') as image:
                images.append(image)

        width, height = images[0].size
        blendedImage = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        totalWeight = sum(2 ** i for i in range(len(images)))
        for i, image in enumerate(images):
            weight = 2 ** (len(images) - i - 1) / totalWeight
            blendedImage = Image.blend(blendedImage, image, 2 * weight)

        for i in images:
            i.close()

        return blendedImage.convert('RGB')
