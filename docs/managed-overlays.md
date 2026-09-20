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

## Stock drift baseline

Recorded 2026-09-20 against Omarchy 4.0.4-1 (system moved 4.0.3-1 →
4.0.4-1 with no overlay breakage):

* notifications `Service.qml`: `11665542e70df80ccd3c785a6143dee2daefd2082e4f75c740adc2c9947cf7c2`
* notifications `components/NotificationCard.qml`: `3f023446cfe26b9f70570d7088baab31e56ca374c4a206a7c098b09d36cdff3d`
* menu `Menu.qml`: `0154d0ec3855fbb48aa06eaa724a19f3c07c377494d4a3de65daed2d7d9100e3`
* Applier re-verified clean against this stock (exit 0, idempotent
  re-run prints "already applied"); vendored `Menu.qml` still
  qmllint-clean against current shell imports.

After any future `omarchy update`: re-run `./tests/test.sh` (the
notifications overlay test applies to fixture copies of live stock and
fails loudly on drift) and compare fresh `sha256sum`s against the above.
If the anchor blocks moved, re-record `overlays/rowdy.menu/Menu.qml` from
a fresh clone plus chrome edits; if only the card changed, no action needed
(the card is fully vendored).
