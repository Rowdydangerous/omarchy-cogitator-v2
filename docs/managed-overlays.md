# Managed clone overlays

Some Cogitator surfaces cannot be themed from a third-party plugin: the
shell shares no view API for notification cards or menu chrome. For those,
and only those, the project manages user-owned clones:

| Clone | Source | Overlay (this repo) | Change |
|---|---|---|---|
| `*.notifications` | `omarchy.notifications` | `overlays/notifications/NotificationCard.qml` + `scripts/apply-notification-overlay.py` (3-line centering patch) | centered herald cards, bracket frame, chamfer, severity tab |
| `*.menu` | `omarchy.menu` | `overlays/rowdy.menu/Menu.qml` (full file) | bracket frame, chamfer, mono caps chrome, apps → Application Cogitator, Left-at-root escapes to the Command Nexus, unified 560px card |

## Lifecycle (transactional, like everything else)

* `cogitator enable` snapshots first: a pre-existing clone's touched
  files are backed up under state; a missing clone is created with
  `omarchy plugin clone`. Then overlay files are stamped and a receipt
  marker (`.cogitator-v2-herald` / `.cogitator-v2-menu`) is written.
* `cogitator disable` restores exactly what was captured: prior files
  byte-for-byte, or native `plugin remove` for a clone we created
  (receipt-guarded; foreign changes are left alone with a warning).
* The notifications anchor patch fails loudly on upstream drift instead
  of half-applying. The full-file menu overlay is re-recorded from a
  fresh clone when upstream refactors (diff, re-apply chrome, commit).
* `omarchy plugin remove <clone>` at any time falls back to stock
  instantly — the escape hatch if an Omarchy update ever breaks a restyle.

## Why clones instead of theme tokens

Theme `colors.toml`/`shell.toml` already carry everything token-driven
(bar, popups, tooltips, notifications colors, menu colors, lock, OSD).
Clones exist only where geometry and behavior live in first-party QML:
card shape/position, menu chrome, app-launch routing. Colors still come
from theme tokens, so palettes flow through automatically.

## Proof

* `docs/screenshots/notification-herald.png` — critical toast, centered.
* `docs/screenshots/command-menu*.png` — root rites, apps chamber,
  stock delegation.
