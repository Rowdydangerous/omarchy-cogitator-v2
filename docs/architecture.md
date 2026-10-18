# Cogitator replacement suite

## Scope

The primary goal is a reversible, stock-based replacement suite for all Omarchy
Quickshell surfaces. Copy stock behavior first, then style one surface at a time.
The console, burn and CRT effects support this suite. Terminal prompt styling is
an optional extra.

See `widget-inventory.md` for the full catalogue and current runtime-use map.

## Current implementation boundary

* `plugins/`: all 37 installed first-party plugins, imported as unstyled baselines.
  Each root manifest uses `cogitator.<name>` and `omarchy.clonedFrom`.
* `qml/`: existing working custom service, console, burn, Nexus and launcher.
* `overlays/`: existing menu and notification styling, applied to staged suite
  plugin copies at installation. Keeping the stock baselines separate lets us
  compare styling against upstream behavior.
* Root theme files: native-installable green theme outputs. They must remain at
  the root while native installation uses this repository directly.
* `palettes/`: color sources and renderer; `themes/`: generated alternate themes.
* `config/`: supported defaults; `hypr/`: compositor shader template.
* `shared/frames/`: reusable chamfered frame and pinned popup/dialog components,
  packaged locally into affected plugins by the installer.
* `shared/voice/`: Mechanicus interface vocabulary, status litanies and catalogue
  names, applied to presentation bindings without changing backend models.
* `shared/icons/`: native vector bar identity icons with functional states,
  locally packaged into the affected plugins.
* `scripts/`: lifecycle and import tooling; `tests/`: regression checks.
* `extras/`: manually installed additions outside the core Quickshell scope.
* `docs/reference/`: font and microcopy research, not runtime loaders.

`cogitator enable` now installs and switches the suite. The old two-clone
restoration path remains only for engagements created before this migration.

## Import and upstream maintenance

`python3 scripts/import-stock-plugins.py` copies the installed stock release,
following Omarchy's clone-path convention. It refuses to overwrite `plugins/`.
`docs/stock-baseline.json` records source manifests, release, status, and file
hashes before identity changes. Stock attribution remains in each manifest.

QML continues to use the host's `qs.Ui`, `qs.Commons`, and service APIs. Importing
plugins does not fork the Quickshell host. Future shared Cogitator components
must be packaged inside each installed plugin or exposed through a verified
import path. A repository-level shared folder alone is not an installation API.

The full bar baseline contains its stock widget files too; those support the
stock bar engine. Individual widget baselines are separate replacement plugins.

## Activation implementation

`scripts/cogitator-suite.py` implements:

1. Installation of individual replacement directories with ownership receipts.
2. Snapshot of actual enabled state, bar selection, placements, per-instance
   settings, and existing user clones, including initially absent shell.json.
3. Replacement only of currently active components; optional plugins stay off.
4. Explicit handling of existing custom clones rather than silently replacing
   or deleting them. Backups must distinguish original files from our overlays.
5. Journaled rollback of plugin routing and layout as well as the wrapper's
   theme restoration. With no engaged edits, shell.json returns byte-for-byte;
   unrelated changes are retained through a three-way undo.
6. Source refresh through `cogitator apply`, with receipt checks and permanent
   backups before managed installs are replaced.

Tests cover repeated instances, custom clones, moved widgets, changed settings,
absent configuration, collisions and failed installation. See
`suite-switching.md` for runtime checks and recovery behavior.

Keep lock/PAM and Polkit authentication behavior identical while styling their
presentation. Keep idle, battery and night-light service semantics identical.
Include dev-gallery as a review baseline, not an automatically active widget.

## Styling sequence

Menu/launcher and notifications → bar/workspaces/clock → audio/network/Bluetooth/
power → remaining panels and overlays → lock and authentication presentation.

## Deferred visual ideas

Independent scanline toggle, phosphor glow, bloom, vignette toggle, background
data density/speed, holographic master switch and text speed are not implemented
settings. They were removed from the configuration example. Existing user files
are preserved; any old reserved keys remain inert.
