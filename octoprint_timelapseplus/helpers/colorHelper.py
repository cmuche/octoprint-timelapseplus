class ColorHelper:

    @staticmethod
    def hexToRgba(hexVal, transparency):
        try:
            hexVal = hexVal.lstrip('#')
            rgb = tuple(int(hexVal[i:i + 2], 16) for i in (0, 2, 4))
        except Exception:
            rgb = (0, 0, 0)

        alpha = int(transparency * 255)
        return rgb + (alpha,)
