![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/logo-small.png)

![GitHub release (latest by date)](https://img.shields.io/github/v/release/cmuche/octoprint-timelapseplus?label=Latest%20Version)
![GitHub Release Date](https://img.shields.io/github/release-date/cmuche/octoprint-timelapseplus?label=Release%20Date)
![GitHub repo size](https://img.shields.io/github/repo-size/cmuche/octoprint-timelapseplus?label=Size)

Timelapse+ is a powerful yet lightweight plugin to capture, enhance and render your print timelapses.

| [![Video](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/timelapseplus.gif)](https://www.youtube.com/watch?v=zs9QcQsIEyM) |
|------------------------------------------------------------------------------------------------------------------------------------------------|
| Click the image to see the video                                                                                                               |                                                                                                               |

# 👀 Examples 
Check out the [_Examples Page_](https://github.com/cmuche/octoprint-timelapseplus/wiki/Examples)

# 🚀 Features
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
- __Pre-Roll__ and __Post-Roll__ effects
  - __Still frame__ / __Short timelapse__ / __Final preview__
  - __Animated__
  - Show __print file name__ and __information__ at the beginning
- Add __Timecode__ information
  - Many variations
    - Text
    - Time
    - Elapsed time
    - Analog clock
    - Progress bar
   - Customizable __colors__
   - Customizable __position__ and __size__
- Colorful __Fade-In__ and __Fade-Out__ effects
- Manage and set up your enhancement- and render presets via the settings page
- Snapshots are stored in __Frame Collections__, so you can re-render them at any time with different settings and presets
- __Preview__ the __snapshot capturing__ live while printing
- Multiple __Output Formats__ and __Codecs__ with different __Quality Presets__
  - __MP4__ (H.264 and H.265)
  - __GIF__
  - __WebM__ (VP8 and VP9)
  - Legacy __AVI__ and __MPG__
- Supports __Webcam Snapshot Endpoints__ as well as __Webcam Streams__
  - __JPEG Snapshots__
  - __MJPEG__ Streams
  - __MP4__ Streams
  - __HLS__ Streams
- __Purge__ Videos and Frame Collections after `n` days
- Timelapse+ __doesn't modify your GCODE__ and __doesn't affect your printer's movements__!

# 📚 Wiki
You can find the Documentation and Help on the [Timelapse+ Wiki Pages](https://github.com/cmuche/octoprint-timelapseplus/wiki).

# 🖥️ Screenshots

### File Manager
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/files.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/files.png)

### Current Print Job
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/current-print.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/current-print.png)

### Render Jobs Overview
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/render-jobs.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/render-jobs.png)

### Render Preview
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/render-preview.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/render-preview.png)

### Settings Page
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-general-1.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-general-1.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-general-2.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-general-2.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-enhancement.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-enhancement.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-render-1.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-render-1.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-render-2.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-render-2.png)

### More Features
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-test-capture.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-test-capture.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-live-preview.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/settings-live-preview.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/prerequisites.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/prerequisites.png)
[![](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/toast.png)](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/screenshots/toast.png)
