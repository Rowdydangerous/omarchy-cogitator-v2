# Enable-time crash regression (2026-10-16/17)

## Evidence

Quickshell 0.3.1 with Qt 6.11.2 repeatedly segfaulted in `__dynamic_cast` during
QML finalization/incubation. RTTI from the first core identified a cast from
`EngineGenerationExt` to `qs::io::ipc::IpcHandlerRegistry`. The fault coincided
with an IPC exit request immediately after selecting the replacement services.
This suggests an object-lifetime/reload/shutdown overlap; missing Quickshell
function symbols prevent establishing the precise faulty source line.

The issue was first noticed after introducing the controller's SVG/MultiEffect
icon. That rendering path was removed as an isolation step. A subsequent cycle
still produced dump PID 188186 with the same stack signature, so the icon alone
was not sufficient to explain or fix the recurrence.

## Changes

* The control uses its original font-rendered icon path, now with a cog glyph.
  The SVG is retained only as an unused design asset.
* Runtime QML staging uses a top-level hidden directory under the plugins
  directory, rather than a hidden directory inside the live coordinator root.
  Omarchy ignores the former; the latter generated reload events for temporary
  copies, including no-op deployments.
* Enable no longer activates the coordinator separately before selecting the
  suite. The suite's atomic configuration already includes it.
* Enable no longer requests a shell exit while the replacement QML/IPC objects
  are being incubated. Newly enabled services mount from the config change.
  Explicit source-development refresh remains separate.

## Verification and limits

Regression tests cover staging location, staging cleanup, font-only icon
rendering and an enable path without separate coordinator activation or a final
shell restart. The full regression suite passed.

The first SVG-rollback/staging-only live test failed and is retained as
`backups/enable-stability-1792244859134105494.json` in the state directory.
After removing the enable-time restart overlap, the next disable/enable cycle
passed with a 15-second observation window and no new coredumps:
`backups/enable-stability-1792246010942647249.json`.

This verifies the observed cycle, not immunity to all Quickshell crashes.
If the symptom returns, compare the new dump and transition logs rather than
assuming the icon is responsible. No upstream issue has been filed.

## Native emblem restoration

After the transition fix, the skull-and-cog design was restored in
`control/CogSkull.qml` using native rectangles and a filled Qt Quick vector path.
The SVG image and MultiEffect/offscreen texture pipeline remain unused.
The controller packaging checks passed. A further disable/enable cycle with this
emblem passed its 15-second observation with no new coredumps:
`backups/enable-stability-1792246443813401880.json`. The restored emblem was
visually checked beside the clock after that cycle.
