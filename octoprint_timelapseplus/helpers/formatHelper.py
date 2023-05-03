from ..model.format import Format


class FormatHelper:
    @staticmethod
    def getDefaultVideoFormat():
        formats = FormatHelper.getVideoFormats()
        return next(x for x in formats if x.ID == 'mp4-h264-nq')

    @staticmethod
    def getVideoFormats():
        return [
            Format('mp4-h264-lq', 'MP4', 'Low Quality', 'mp4', 'video/mp4', 'H264', 'libx264', {'-crf': '28', '-preset': 'medium'}),
            Format('mp4-h264-nq', 'MP4', 'Normal Quality', 'mp4', 'video/mp4', 'H264', 'libx264', {'-crf': '23', '-preset': 'slow'}),
            Format('mp4-h264-hq', 'MP4', 'High Quality', 'mp4', 'video/mp4', 'H264', 'libx264', {'-crf': '18', '-preset': 'slower'}),

            Format('mp4-h265-lq', 'MP4', 'Low Quality', 'mp4', 'video/mp4', 'H265', 'libx265', {'-crf': '28', '-preset': 'medium'}),
            Format('mp4-h265-nq', 'MP4', 'Normal Quality', 'mp4', 'video/mp4', 'H265', 'libx265', {'-crf': '23', '-preset': 'slow'}),
            Format('mp4-h265-hq', 'MP4', 'High Quality', 'mp4', 'video/mp4', 'H265', 'libx265', {'-crf': '18', '-preset': 'slower'}),

            Format('webm', 'WEBM', None, 'webm', 'video/webm', 'VP9', 'libvpx-vp9', {'-crf': '31', '-b:v': '0'}),

            Format('avi-mpeg4', 'AVI', None, 'avi', 'video/x-msvideo', 'MPEG-4', 'mpeg4', {'-qscale:v': '10'}),

            Format('mpeg2', 'MPEG', None, 'mpg', 'video/mpeg', 'MPEG-2', 'mpeg2video'),

            Format('gif', 'GIF', None, 'gif', 'image/gif', None, None)
        ]

    @staticmethod
    def getVideoFormatExtensions():
        return list(map(lambda x: x.EXTENSION, FormatHelper.getVideoFormats()))

    @staticmethod
    def getVideoFormatById(id):
        formats = FormatHelper.getVideoFormats()
        return next((x for x in formats if x.ID == id), FormatHelper.getDefaultVideoFormat())
