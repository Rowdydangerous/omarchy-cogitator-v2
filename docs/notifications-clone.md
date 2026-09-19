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

## Ownership notes

* The clone is USER config, not package files: `cogitator disable` /
  `uninstall` never touch it. It works engaged or not.
* Drift caveat: a future Omarchy update may refactor the stock service.
  If toasts break after `omarchy update`, diff
  `/usr/share/omarchy/shell/plugins/notifications/` against the clone and
  re-apply the two changes above, or `omarchy plugin remove
  rowdy.notifications` to fall back to stock instantly.
* Proof: `docs/screenshots/notification-herald.png` (critical toast,
  centered, glow fill, tab, brackets, chamfer).
