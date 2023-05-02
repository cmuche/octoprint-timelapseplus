from ..model.format import Format


class FormatHelper:
    @staticmethod
    def getVideoFormats():
        return [
            Format('mp4-h254', 'MP4', None, 'mp4', 'video/mp4', 'H264', 'libxh264'),
            Format('mp4-h265', 'MP4', None, 'mp4', 'video/mp4', 'H265', 'libx265'),
            Format('webm', 'WEBM', None, 'webm', 'video/webm', 'VP9', 'libvpx-vp9', {'-crf': '15', '-b:v': '0'}),
            Format('avi-mpeg4', 'AVI', None, 'avi', 'video/x-msvideo', 'MPEG-4', 'mpeg4'),
            Format('mpeg2', 'MPEG', None, 'mpeg', 'video/mpeg', 'MPEG-2', 'mpeg2video'),
            Format('gif', 'GIF', None, 'gif', 'image/gif', None, None)
        ]

    @staticmethod
    def getVideoFormatExtensions():
        return list(map(lambda x: x.EXTENSION, FormatHelper.getVideoFormats()))

    @staticmethod
    def getVideoFormatById(id):
        formats = FormatHelper.getVideoFormats()
        return next(x for x in formats if x.ID == id)
