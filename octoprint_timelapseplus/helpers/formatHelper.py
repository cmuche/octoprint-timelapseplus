from ..model.format import Format


class FormatHelper:
    @staticmethod
    def getDefaultVideoFormat():
        formats = FormatHelper.getVideoFormats()
        return next(x for x in formats if x.ID == 'mp4-h264-hq')

    @staticmethod
    def getVideoFormats():
        return [
            Format('mp4-h264-prevq', 'MP4', 'Draft Quality', 'mp4', 'video/mp4', 'H.264', 'libx264', {'-movflags': '+faststart', '-crf': '45', '-preset': 'ultrafast'}),
            Format('mp4-h264-lq', 'MP4', 'Low Quality', 'mp4', 'video/mp4', 'H.264', 'libx264', {'-movflags': '+faststart', '-crf': '35', '-preset': 'veryfast'}),
            Format('mp4-h264-nq', 'MP4', 'Normal Quality', 'mp4', 'video/mp4', 'H.264', 'libx264', {'-movflags': '+faststart', '-crf': '30', '-preset': 'veryfast'}),
            Format('mp4-h264-hq', 'MP4', 'High Quality', 'mp4', 'video/mp4', 'H.264', 'libx264', {'-movflags': '+faststart', '-crf': '25', '-preset': 'veryfast'}),
            Format('mp4-h264-uq', 'MP4', 'Ultra Quality', 'mp4', 'video/mp4', 'H.264', 'libx264', {'-movflags': '+faststart', '-crf': '20', '-preset': 'veryfast'}),

            Format('mp4-h265-lq', 'MP4', 'Low Quality', 'mp4', 'video/mp4', 'H.265', 'libx265', {'-crf': '35', '-preset': 'veryfast'}),
            Format('mp4-h265-nq', 'MP4', 'Normal Quality', 'mp4', 'video/mp4', 'H.265', 'libx265', {'-crf': '30', '-preset': 'veryfast'}),
            Format('mp4-h265-hq', 'MP4', 'High Quality', 'mp4', 'video/mp4', 'H.265', 'libx265', {'-crf': '25', '-preset': 'veryfast'}),
            Format('mp4-h265-uq', 'MP4', 'Ultra Quality', 'mp4', 'video/mp4', 'H.265', 'libx265', {'-crf': '20', '-preset': 'veryfast'}),

            Format('webm-vp9-prevq', 'WebM', 'Draft Quality', 'webm', 'video/webm', 'VP9', 'libvpx-vp9', {'-crf': '60', '-b:v': '0'}),
            Format('webm-vp9-lq', 'WebM', 'Low Quality', 'webm', 'video/webm', 'VP9', 'libvpx-vp9', {'-crf': '50', '-b:v': '0'}),
            Format('webm-vp9-nq', 'WebM', 'Normal Quality', 'webm', 'video/webm', 'VP9', 'libvpx-vp9', {'-crf': '40', '-b:v': '0'}),
            Format('webm-vp9-hq', 'WebM', 'High Quality', 'webm', 'video/webm', 'VP9', 'libvpx-vp9', {'-crf': '30', '-b:v': '0'}),
            Format('webm-vp9-uq', 'WebM', 'Ultra Quality', 'webm', 'video/webm', 'VP9', 'libvpx-vp9', {'-crf': '20', '-b:v': '0'}),

            Format('webm-vp8-lq', 'WebM', 'Low Quality', 'webm', 'video/webm', 'VP8', 'libvpx', {'-crf': '50', '-b:v': '0'}),
            Format('webm-vp8-nq', 'WebM', 'Normal Quality', 'webm', 'video/webm', 'VP8', 'libvpx', {'-crf': '40', '-b:v': '0'}),
            Format('webm-vp8-hq', 'WebM', 'High Quality', 'webm', 'video/webm', 'VP8', 'libvpx', {'-crf': '30', '-b:v': '0'}),

            Format('avi-mpeg4-lq', 'AVI', 'Low Quality', 'avi', 'video/x-msvideo', 'MPEG-4', 'mpeg4', {'-qscale:v': '22'}),
            Format('avi-mpeg4-nq', 'AVI', 'Normal Quality', 'avi', 'video/x-msvideo', 'MPEG-4', 'mpeg4', {'-qscale:v': '10'}),
            Format('avi-mpeg4-hq', 'AVI', 'High Quality', 'avi', 'video/x-msvideo', 'MPEG-4', 'mpeg4', {'-qscale:v': '2'}),

            Format('mpeg2-lq', 'MPEG', 'Low Quality', 'mpg', 'video/mpeg', 'MPEG-2', 'mpeg2video', {'-qscale:v': '22'}),
            Format('mpeg2-nq', 'MPEG', 'Normal Quality', 'mpg', 'video/mpeg', 'MPEG-2', 'mpeg2video', {'-qscale:v': '10'}),
            Format('mpeg2-hq', 'MPEG', 'High Quality', 'mpg', 'video/mpeg', 'MPEG-2', 'mpeg2video', {'-qscale:v': '2'}),

            Format('gif', 'GIF', None, 'gif', 'image/gif', None, ['gif', 'png'], {'-i': 'palette.png', '-filter_complex': '[0:v][1:v]paletteuse'}, True),
            Format('gif-nopalette', 'GIF', 'Low Quality', 'gif', 'image/gif', None, ['gif', 'png'])
        ]

    @staticmethod
    def getVideoFormatExtensions():
        return list(map(lambda x: x.EXTENSION, FormatHelper.getVideoFormats()))

    @staticmethod
    def getVideoFormatById(id):
        formats = FormatHelper.getVideoFormats()
        return next((x for x in formats if x.ID == id), FormatHelper.getDefaultVideoFormat())
