# Shared Cogitator frame chrome

`FrameSurface.qml` is the common outer frame: a filled bottom-right chamfer,
two-pixel outline, and three 18-pixel corner flares. Small cards reduce the cut
depth to fit. Colors follow the active theme and retain dynamic stock border
colors (for example authentication errors).

The other QML files are pinned copies of Omarchy's popup/dialog components,
with their outer surface replaced. `upstream.json` records their source hashes.
Focus, placement, outside-click dismissal, input handlers and animations stay
in those copies; buttons, sliders and list-row styling remain stock.

`scripts/frame-style.py` packages these files inside each affected plugin's
`frames/` directory and qualifies its imports. This avoids reliance on an
uninstalled global QML module. Changes deploy through `cogitator apply`.
Source plugin baselines remain available for upstream comparison.

Coverage includes bar popups, tray/media cards, tooltips, clipboard, emoji,
reminder and confirmation dialogs, OSD, image picker, Wi-Fi QR, speed-test
overlays, lock input and Polkit cards. Existing menu/Nexus/launcher/notification
outlines are kept, with their rectangular fill replaced by the same cut shape.
The console also uses the shared frame.

`tests/frames.py` checks packaging for 25 plugins, local import paths, shared
component QML, and the three custom console/menu/launcher surfaces.
For stock panels that already return a diagnostic-free lint failure, the test
compares the original and framed versions and rejects new diagnostics. Shared
components and the custom surfaces are required to lint successfully.
Authentication presentation is linted; tests do not initiate authentication.

Audio and clock popups were visually checked live after deployment; the running
shell and a notification smoke check produced no frame-related QML errors.

The one-time `python3 scripts/frame-style.py` import refuses to overwrite pinned
files. For upstream updates, compare the source components against their hashes
and review behavior changes before updating the copies.
