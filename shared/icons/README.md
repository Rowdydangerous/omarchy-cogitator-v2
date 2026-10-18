# Industrial identity icons

These native QML vectors establish the suite's machinery language while keeping
functional silhouettes readable at bar size. No image loader, offscreen layer,
MultiEffect or decorative animation is used.

* `VoxIcon.qml`: armored speaker/grille, level-dependent sound waves, mute slash,
  missing-device dimming and a headphone silhouette for headphone output.
* `RelayIcon.qml`: transmission mast with five signal-strength states, a hardline
  connector for Ethernet, and a severed-link slash when disconnected.
* `PowerCellIcon.qml`: industrial cell with proportional charge fill, charging
  bolt and a supply-coupler silhouette when no battery exists. The adapter binds
  critical discharging reserves to the urgent theme color.
* `IconState.js`: display-state thresholds and bounded measurement helpers.
* `GlyphIcon.qml`: legacy font symbols fitted to their painted bounding box,
  sharing the vectors' 82% optical footprint rather than their font's em size.
* `MachineSigil.qml`: Bluetooth rune with broken-cog surround and connection
  mark; armored microphone with mute/in-use states; mounted display with
  brightness and multiple-display details; maintenance cog/data arrow; herald
  bell with DND slash; data-slate; and a chrono dial.
* `WeatherIcon.qml`: angular sun/moon, partial cloud, cloud, fog, rain, snow,
  sleet and storm symbols. Unknown conditions use an explicit unknown marker.
  Classification consumes the stock weather resolver's glyph, preserving its
  source and day/night decisions rather than guessing from location or time.

Colors follow the bar theme. Text tooltips combine the rite name with the familiar
function and current state. Right-click/scroll actions remain stock. The power
widget retains its optional percentage readout and allocates space for it.

`scripts/icon-style.py` applies these to the audio/network/power bar buttons when
staging installs, after frame and copy styling. Stock source/model files remain
available for comparison. Popup controls and device names are not replaced.

`tests/icons.py` checks state thresholds, invalid measurement handling, source
drift detection, model preservation, interaction handlers and icon packaging.
The new vectors pass Qt 6 checks; patched stock panels are compared against
their existing lint diagnostics.

Live review checked the bar's current mute, wireless and battery-percentage
states after a single source-loading shell restart. Further identity icons can
reuse the same weight, cut corners and mounting details without changing the
functional language of controls.

The extended pass adds Bluetooth, microphone, display, weather, update and DND
bar icons. Updates retain their pending-only visibility; the DND indicator
retains its active/inactive reveal behavior. It also places the data-slate in
Clipboard's search header and a dial in Clock's popup. The bar time readout,
clipboard contents and all selection/action handlers remain unchanged.

Vectors and the controller emblem use an 82% optical footprint. Legacy idle,
night-light, dictation, recording, reminder and agent glyphs use the same
painted-bounds fitting. Their active/inactive opacity and reveal behavior remain
unchanged, so inactive indicators are still deliberately dimmed.

`scripts/layout-style.py` gives Weather a stacked temperature/location/stats
layout with bounded equal-width columns and wrapping labels. The shorter
"Thermal Feel" label avoids the previous overlap caused by long rite copy.

The Dictation indicator launches the floating `voxtype configure` terminal
directly. The stock `omarchy-voxtype-config` helper unconditionally restarts
Quickshell after that terminal closes. Cogitator instead restarts only its
Voxtype status follower, preserving updated status without flashing the bar.

Live review checked the extended bar set, the Clock dial/date alignment and
Clipboard's header without capturing its history contents. Source changes were
loaded with one shell restart, without a theme change.
