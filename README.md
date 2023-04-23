# Timelapse+ for OctoPrint

Timelapse+ is a powerful yet lightweight plugin to capture and render your print timelapses.

| [![Video](https://github.com/cmuche/octoprint-timelapseplus/raw/master/assets/timelapseplus.gif)](https://www.youtube.com/watch?v=fV8yoPwcXAU) |
|------------------------------------------------------------------------------------------------------------------------------------------------|
| Click the image to see the video                                                                                                               |                                                                                                               |

## Features
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
- Timelapse+ __doesn't modify your GCODE__ and __doesn't affect your printer's movements__!