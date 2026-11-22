# Persistent Control Sanctum

## Install and open

```bash
cogitator install
omarchy-shell cogitator.control open
omarchy-shell cogitator.control page Appearance
```

Installation adds `cogitator.control` immediately before the clock, following
its actual bar section and a stock/custom clock clone. If no clock exists it
uses the center section. Reinstalling preserves an existing placement. It does
not engage the theme; suite/theme files are deployed on the first engagement.
Use the wrapper installer rather than adding the service plugin alone through
the native plugin manager: the native installer accepts one plugin root and
does not execute suite installation hooks.

Left-click the cog/sigil to open the chamfered control panel. The icon is muted
when disengaged, marked when engaged, pulses during transitions and turns amber
on a failed controller operation.

## Pages

* **Overview**: Engage/Disengage, current palette, transition status and failure
  details, plus **Update from GitHub** (the same worker as `cogitator update`).
  Switching mode restarts terminals as part of Omarchy theme changes.
* **Appearance**: palette swatches, custom hex/RGB picker, local/global CRT,
  intensity and application-window chamfers.
* **Surfaces**: console placement/opacity, background burn, workspace rites and
  communique streaming/typing speed (20–200 ms per character; higher is slower).
* **Motion**: Minimal/Normal/Full, flicker, grain, sweep persistence/ghosting,
  edge falloff and SIGMA-IX watermark.

Palette choices use the display names **Imperium** (`green`), **Ryza** (`amber`),
**Holy Mars** (`red`), and **Metalica** (`industrial`). Names are centralized in
`control/settings-schema.json`; saved IDs and theme paths are unchanged.

All 22 supported settings are exposed. Reserved settings are not presented.
Old out-of-range hand-edited values are displayed at their effective renderer
bounds without rewriting the file merely by opening the panel.

## Apply and Revert

Edits stay in a local draft until Apply. Revert reloads the saved configuration.
While disengaged, Apply saves for the next engagement without restarting the
shell or enabling effects. While engaged, Apply batches changes into a detached
live-settings transition. The running service watches the rendered config;
ordinary settings do not redeploy plugins or restart Quickshell. Only changes
to global CRT/window geometry reload their compositor settings. Palette changes
retint the theme without an additional source refresh or shell restart.

Only changed keys are written; unrelated keys and comment lines are retained.
The backend validates types/ranges/colors and backs up the original config before
saving. A content revision prevents overwriting edits made outside the panel.
Changing mode requires first applying or reverting a dirty draft.

The backend launches commands with argv arrays, not constructed shell input.
Transitions run in `cogitator-v2-transition.service`; their running/completed/
failed status is retained in `control-operation.json`, surviving shell and
terminal restarts. The panel can show recent transition logs after a failure.

## Persistent lifecycle

The controller is independent of `cogitator-rite` and the 37 replacement roots.
It remains enabled through disengagement. Installing it during an existing
engagement rebases both sides of that suite journal to include the persistent
widget; the original pre-rebase journal is retained in recovery storage.

The controller's source manifest is `control/manifest.json.in`; installation
materializes it as `manifest.json` in the staged plugin. This keeps the public
repository's root manifest as its sole marketplace entry without changing the
installed controller's plugin ID or behavior.

`cogitator uninstall` removes the unchanged receipted controller through native
plugin removal, including its bar reference. Edited installations are preserved.
Install/config/suite backups are retained under the Cogitator state directory.

The installed widget contains its backend and frame copies plus a project-path
receipt. Keep the project checkout available: it supplies the manager and suite
sources, like the existing `cogitator` PATH shim.

## Verification

`tests/control.py` covers schema completeness, hex/comment parsing, input bounds,
preservation of old effective values, changed-key saves, revision conflicts,
custom clock placement, repeated clock instances, suite rollback, active-journal
rebasing and controller packaging. Qt 6 syntax checks match Quickshell's runtime;
the older system Qt 5 parser is not used for this component.

`tests/control-layout.py` runs the actual controller and shared popup with the
host's `PluginBarApi` in an isolated headless Sway session. Install `sway` as a
development-only test dependency to run it; no Sway configuration or session is
needed for normal Cogitator use. The test uses software rendering, a separate
Wayland socket, and a stub controller backend, so it never engages the real
desktop or saves user settings. It covers all controller pages, both engagement
states, 500/1000-pixel-tall outputs, four bar edges, legacy strip windows, and
native full-screen windows reserving a 64-pixel strip with a 26-pixel facade size.
It checks visible/reachable Engage and Apply controls and their dispatched
actions. Without Quickshell or Sway, this integration test is explicitly skipped.

For installed widgets whose bar facade lacks `barSizeFor`, the shared popup uses
the anchor window's public `exclusiveZone` to clear the actual per-output strip,
including a notch floor. Configured size remains the fallback for older bars
with no explicit reserved zone. Theme colors are namespace-qualified to avoid
collisions with toolkit types.

Installer integration tests also run the real controller CLI in temporary
config/state trees: upgrading an older receipted controller retains exact user
configuration and recovery copies, while an edited installation is refused
without writing files or invoking shell IPC.

Live verification on 2026-10-08 confirmed the widget and Appearance panel while
disengaged. `verify-control.py`, run detached, completed an engagement and
disengagement through the controller backend and confirmed the widget remained
enabled immediately before the clock in all three states. Proof is retained at
`backups/control-proof-1791513876381727194.json` in the Cogitator state directory.

On 2026-10-09 the live-settings proof toggled/restored a workspace setting through
the controller backend. Quickshell kept PID 175458 throughout (zero restarts),
the rendered setting updated correctly, and original config bytes were restored.
The proof is saved as `backups/live-settings-proof-1791595020002113666.json`.
