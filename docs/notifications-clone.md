# Notifications herald: rowdy.notifications clone

Stock Omarchy notifications render top-right through the first-party
`omarchy.notifications` service. A third-party plugin cannot restyle them
(the shell shares no notification view API), so this uses Omarchy's own
clone mechanism — the single sanctioned takeover path:

```bash
omarchy plugin clone omarchy.notifications
# → ~/.config/omarchy/plugins/rowdy.notifications (clonedFrom routing,
#    replaces the built-in automatically)
```

## What the clone changes (and only this)

* `components/NotificationCard.qml` — rewritten as the Cogitator herald:
  corner-bracket framing, chamfered bottom-right corner (Shape path),
  severity tab straddling the top edge (CRITICAL / ADVISORY / NOTICE),
  glowing phosphor fill + dark text for critical alerts, dark fill +
  phosphor text otherwise, machine-monospace typography. Same
  props/signals contract as stock, so daemon, history, timeouts, DND,
  and actions are untouched. Colors come from `Color.notifications.*`
  tokens, so every palette flows through automatically.
* `Service.qml` popup column — three lines: top-right stack becomes a
  horizontally-centered column at ~22% screen height; card delegates
  center instead of right-aligning. Mask stays on the column (non-modal).

## Managed overlay: herald applies while engaged, prior state on disable

The herald lives in this repo under `overlays/notifications/` (the card)
plus `scripts/apply-notification-overlay.py` (the three-line centering
patch, applied to the clone's Service.qml with drift detection).

* `cogitator enable` snapshots notification state first: if a clone
  already exists, its Service.qml + card are backed up; if none exists,
  one is created with `omarchy plugin clone`. Either way the overlay is
  stamped (receipt `.cogitator-v2-herald`) and the shell restarts.
* `cogitator disable` restores exactly what was captured: pre-existing
  clone files are put back byte-for-byte; a clone we created is removed
  via native `plugin remove` (receipt-guarded) so stock resumes.
* Drift caveat: if upstream refactors the stock service, the applier
  fails loudly instead of half-applying. Re-record the overlay against
  the new stock, or `omarchy plugin remove rowdy.notifications` to fall
  back to stock instantly.
* Proof: `docs/screenshots/notification-herald.png` (critical toast,
  centered, glow fill, tab, brackets, chamfer).
