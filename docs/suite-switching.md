# Suite installation and reversible switching

## Commands

```bash
cogitator enable       # snapshot, install 37 roots, switch enabled components
cogitator suite status # full journal: phase, selected plugins and original state
cogitator apply        # deploy source changes without replacing the snapshot
cogitator disable      # restore routes, layout, theme and background
cogitator uninstall    # remove inactive managed installs; keep user config
```

Enable/disable run in `cogitator-v2-transition.service`. Theme switches restart
terminals, including OpenCode if it runs inside one. The detached transition
continues. Reopen the terminal and inspect status and logs:

```bash
cogitator status --json
journalctl --user -u cogitator-v2-transition.service --no-pager -n 60
```

`cogitator apply` restarts Quickshell without switching the theme, so normal
widget styling iterations avoid the terminal restart.

## Installation

Each `plugins/<name>/` root is installed separately into
`~/.config/omarchy/plugins/cogitator.<name>/`. Installation stages complete
directories, validates manifests, and checks discovery before switching config.
Menu and notification styling is applied to staged copies, leaving baseline
sources available for review. Installed receipts record file hashes.

Existing custom clones are never overwritten or removed. During engagement,
their enabled routes and layout entries point at the suite replacement instead;
the original IDs, files and settings remain available for rollback. Unrelated
third-party plugins remain enabled. A foreign or locally modified directory
using a suite ID is preserved and blocks replacement of that directory.

Unused bar widgets and disabled services remain inactive. Mixed widget/service
plugins follow their captured enabled state rather than being added arbitrarily.
The selected stock or stock-cloned bar is replaced; an unrelated custom bar is
left selected.

Enable selects the suite through the config watcher without a final shell
restart. Quitting immediately after selection caused an observed QML/IPC
incubation crash; see `enable-crash.md` for evidence and regression checks.

## Configuration transaction

`~/.local/state/cogitator-v2/suite.json` is written **before** native installers
change shell.json. It records:

* Original bytes, file mode and whether shell.json existed.
* Effective config and plugin enabled-state catalogue.
* Planned config, source/clone ID mappings and selected replacements.
* Installation progress and recovery backup location.

Switching writes shell.json atomically. Every instance in every layout section
is remapped independently: order, sizes, indicator subsets, clock formats and
other inline settings are retained. Bar selection and center anchor are remapped
along with plugin routes. Original implementations are disabled while their
replacements are selected, avoiding competing clone routes.

Disable restores the original config byte-for-byte when it is otherwise
unchanged, including restoring an originally absent file to absence. When
settings or layout change during engagement, a three-way undo reverses our
routing changes while retaining unrelated edits, widget settings and moves.
If differently customized clones become indistinguishable after editing their
repeated instances, restoration refuses to guess and keeps the journal.

Config is backed up again before rollback. The journal is archived only after
the wrapper restarts the restored shell successfully. Backups remain under
`~/.local/state/cogitator-v2/backups/suite-<timestamp>/`.

Suite plugin files remain installed but inactive after disable, ready for the
next enable. Uninstall removes only unchanged receipted copies. Recovery uses
`cogitator disable` even after a failed/partial engagement; do not delete the
journals manually. A pre-suite engagement must be disabled before suite enable.

The independent `cogitator.control` bar widget remains enabled after disable.
It is installed before new snapshots are captured, or explicitly rebased into
both sides of an existing journal, so mode switching never removes its own UI.
See `control-widget.md` for installation and settings.

## Styling workflow

Edit a widget in `plugins/<name>/`, then run `cogitator apply`. It backs up and
refreshes managed copies while retaining the original snapshot and live layout.
Unchanged copies retain their directories and do not trigger file-watch reloads.
Changed copies are fully staged/validated first, then published as a short batch.
This source-development command ends with one intentional shell restart.
The settings panel uses `settings-apply` instead, updating configuration live
without source redeployment or shell restart.
The coordinator's working-tree `qml/` is refreshed too, with checks against its
receipt or pristine native checkout. Direct edits to installed plugin code are
preserved and reported rather than overwritten.

## Compatibility adjustments

* Indicators' dependency URL is relocated after all clone files are copied.
* The cloned bar forwards its approved non-authentication service proxies to
  child-widget facades. Other per-entry methods remain scoped to the entry.
* The custom Nexus focuses each visible window's key catcher, rather than
  referencing an ID outside the window's QML scope.

The host still instantiates its fallback bar, which owns `omarchy.bar` IPC.
Our clone uses a unique IPC target and a debounced inotify watcher so native
visibility commands work even when their IPC nudge reaches the fallback.
The watcher sleeps between filesystem events; it does not periodically poll.
The packaged shell is not modified.

## Verification

`tests/suite.py` uses isolated config/plugin trees and command fixtures. It
covers custom services/widgets, inactive clones, repeated settings, cross-section
moves, disabled components, changed settings, exact-byte/mode restoration,
absent files, re-engagement, collisions, edited installs and validation failure.

`scripts/verify-suite.py` records live selected-plugin state and verifies a
completed restore against the saved input and original catalogue. It can run
detached with `restored <backup-directory> --wait 120` to survive a terminal
restart. Proof JSON is saved alongside recovery backups.

Live activation on 2026-10-02 installed 37 roots and selected 32 replacements;
five unused widgets remained inactive. The cloned audio popup and styled menu
were visually checked. Indicators' load-path error was corrected. The refreshed
running shell had no TypeError, ReferenceError or indicator-loader errors in its
process journal. Idle initialized and Polkit registered; authentication flows
were not exercised by this lifecycle check.

Rapid hide/show was checked with the native bar toggle command and layer geometry.
Its explicit `on`/`off` arguments control the `bar-off` flag: `on` hides, `off`
shows. The final layer returned to the visible screen edge.

The same live cycle restored Osaka Jade, matched every captured prior plugin
enabled state, left all 37 suite plugins inactive, and cleared both journals.
The bar transparency setting changed during engagement and was retained by
rollback. Stock Apps was visually checked with populated application rows and
stock geometry/casing. Proof JSON is retained in that cycle's recovery backup;
exact byte restoration without engaged edits is covered by isolated tests.
