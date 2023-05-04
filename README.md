![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/logo.png)

Timelapse+ is a powerful yet lightweight plugin to capture, enhance and render your print timelapses.

| [![Video](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/timelapseplus.gif)](https://www.youtube.com/watch?v=fV8yoPwcXAU) |
|------------------------------------------------------------------------------------------------------------------------------------------------|
| Click the image to see the video                                                                                                               |                                                                                                               |

# Features
- Trigger snapshots via __commands__ in your GCODE (e.g. on layer change)
  - __@-Commands__ like ``@SNAPSHOT``
  - __Action Commands__ like ``//action:SNAPSHOT`` (on Marlin via ``M118``)
- Regular __time-based__ snapshot mode
- User-friendly and tidy user interface
  - __View, watch and download__ your rendered videos
  - __Preview__ your __render settings__ and check the estimated video length before starting a render job
- Customizable __image enhancements for post-processing__
  - __Brightness__ and __contrast__
  - __Auto-Optimization__ by histogram equalization
  - __Blur__ parts of the video for privacy when sharing
  - Resizing
- __Frame interpolation__ for __smoother timelapses__!
  - __Generate frames__ between your captured frames
  - Based on __motion calculation__ algorithms
  - Or just __blend frames__ together to generate sub-frames
- __Combine/Blend multiple frames__ to reduce the number of total frames
- Colorful Fade-In and Fade-Out effects
- Manage and set up your enhancement- and render presets via the settings page
- Snapshots are stored in __Frame Collections__, so you can re-render them at any time with different settings and presets
- __Preview__ the __snapshot capturing__ live while printing
- Multiple __Output Formats__ and __Codecs__ with different __Quality Presets__
  - __MP4__ (H.264 and H.265)
  - __GIF__
  - __WebM__ (VP8 and VP9)
  - Legacy __AVI__ and __MPG__
- Timelapse+ __doesn't modify your GCODE__ and __doesn't affect your printer's movements__!

# Documentation

## Getting Started
Before you can use Timelapse+ you will have to configure some basic settings. Open the Timelapse+ plugin settings page in OctoPrint.

### Setup FFmpeg, FFprobe and the Webcam URL
In order to render your videos and get information about previously rendered videos, Timelapse+ requires FFmpeg and FFprobe.
You need to install this on your host machine and ensure that OctoPrint is able to access the FFmpeg and FFprobe binaries.
FFprobe is usually bundled with FFmpeg. So when your FFmpeg path is `/usr/bin/ffmpeg` your FFprobe path is probably `/usr/bin/ffprobe`.

### Webcam Snapshot URL
This is the URL which Timelapse+ calls to receive a snapshot.
It has to be callable via HTTP and needs to return a valid JPG/JPEG image.
This is a still image of your live webcam stream.
Currently, Timelapse+ doesn't support other video or image sources, but it is planned for future relaeses.

### Capture Mode and GCODE Preparation
Timelapse+ has two modes to trigger snapshots.
The first is the good old time-based mode, which captures a frame every x seconds.
If you select this mode you can set a timer interval in seconds.

The second option is the command-based mode. With this you can control the snapshot capturing directly from your GCODE.
Whenever a special line (command) is sent to the printer, Timelapse+ will capture a snapshot.
This is powerful if you set up your slicer so that it generates a snapshot command when a layer change occurs.

Timelapse+ supports two types of commands: @-Commands like `@SNAPSHOT` and Action Commands like `M118 //action:SNAPSHOT` or `M118 A1 action:SNAPSHOT`.
A snapshot will be captured when any of these is sent to the printer.
You can read more about Action Commands [here](https://docs.octoprint.org/en/master/features/action_commands.html) and [here](https://marlinfw.org/docs/gcode/M118.html).
The Snapshot Command is customizable so when you enter for examle `CAPTUREFRAME` as the Snapshot Command, Timelapse+ will be triggered whenever it sees `@CAPTUREFRAME` in your GCODE or your printer sends the Action Command `//action:CAPTUREFRAME`. 

### Concepts
... will follow

### Enhancement Presets
... will follow

### Render Presets
... will follow

# Screenshots

### File Manager
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/files.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/files.png)

### Current Print Job
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/current-print.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/current-print.png)

### Render Jobs Overview
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/render-jobs.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/render-jobs.png)

### Render Preview
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/render-preview.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/render-preview.png)

### Settings Page
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-general.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-general.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-enhancement.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-enhancement.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-render-1.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-render-1.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-render-2.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-render-2.png)

### More Features
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/prerequisites.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/prerequisites.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/toast.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/toast.png)
