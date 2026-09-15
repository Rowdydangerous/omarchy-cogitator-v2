# Stretch goal: full Cogitator twin of the Omarchy shell

Pinned at user request. Not started. The Application Cogitator
(`qml/launcher/`) is the reference implementation: own overlay window,
native resolvers underneath, stock plugin untouched, IPC summon, no
keybinding theft.

## Scope when started

Per-surface Cogitator twins, each following the launcher pattern:

* network / audio / bluetooth panels as rite consoles (read-only state +
  stock helpers for persistent actions, as the prop already reads them)
* power cell console with liturgical states (replacing "Spending joules"
  voice — requires cloning `omarchy.power`, the one place cloning is
  justified since its strings live in first-party QML)
* update rite console, weather auspex, tray relic inventory
* lock-screen access console (theme tokens already carry it; twin is optional)

## Rules carried over

* Never edit `$OMARCHY_PATH/shell`; clone only where strings must change.
* Keep kinds honest: service stays service (the menu-kind panel trap is
  documented in Launcher history — claiming `menu` registers a panel entry).
* Service plugins reload only on full shell restart; budget for it.
* Every twin summons via own IPC target; keybindings stay user-owned,
  routed through `scripts/cogitator-menu`-style dispatchers.
* Measure CPU per twin against the tier table in README; stepped motion only.
