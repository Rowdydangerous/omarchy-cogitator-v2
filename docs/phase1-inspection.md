# Phase 1 inspection — 2026-09-14

Machine state (read-only):
* Omarchy `4.0.3-1`, Quickshell `0.3.1`, theme `Osaka Jade`, font `JetBrainsMono Nerd Font`.
* Old project themes still present in `~/.config/omarchy/themes/` (`aether`, `cogitator`, `cogitator-full`); `~/.config/omarchy/plugins/` is empty. Left untouched.
* Live `~/.config/omarchy/shell.json` is stock-default layout, `transparent:true`, `version:1`.

## Plugin mechanism (supported)
* `omarchy plugin add [git-url] [--enable]`, `clone <source-id>`, `enable <id> [placement]`, `disable <id>`, `list`, `remove`, `validate <folder>`.
* Manifest requires `schemaVersion:1`, `id,name,version,kinds,entryPoints`. `entryPoints` must be relative, no `..` or leading `/`.
* `barWidget.defaultSection` must be `left|center|right`.
* User plugins in `~/.config/omarchy/plugins/` auto-reload; force with `omarchy-shell shell rescanPlugins`.
* Never edit `$OMARCHY_PATH/shell/plugins`. Clone instead.

Observed stock plugin IDs/kinds:
* `omarchy.menu`: `menu,bar-widget`
* `omarchy.notifications`: `service`
* `omarchy.osd`: `panel`
* `omarchy.lock`: `service` + `capabilities:[authentication]`
* `omarchy.background`: `service`
* `omarchy.power`, `omarchy.clock`, `omarchy.workspaces`: `bar-widget`
* `omarchy.battery`: `service`
* Full stock list includes background, bar, battery, bluetooth, clock, lock, menu, network, notifications, osd, power, tray, weather, workspaces, etc.

## Theme mechanism
* User theme dir `~/.config/omarchy/themes/<slug>/`. User-written themes unrestricted; cloned-from-git themes drop code files (`*.lua`, terminal configs, `vscode.json`) and regenerate from `$OMARCHY_PATH/default/themed/*.tpl`.
* Stock `osaka-jade` ships `colors.toml` only (no `shell.toml`); `shell.toml` is generated from `default/themed/shell.toml.tpl` into `~/.local/state/omarchy/current/theme/shell.toml`.
* `Color.qml` singleton: `colors.toml` = foundation (`background,foreground,accent,urgent,muted...`), `shell.toml` = per-surface roles (`bar,popups,tooltip,notifications,menu,hyprland,controls,spacing...`).
* Current theme state in `~/.local/state/omarchy/current/theme/` (`colors.toml`, `shell.toml`, `backgrounds/`, `theme.name`).
* Overlay (same slug, few files) vs fork (new slug, full copy). v2 uses fork `cogitator-green`.

## Shell architecture
* `shell.qml` `ShellRoot`: `PluginRegistry`, `BarWidgetRegistry`, `AppLibrary`. User `shell.json` replaces defaults entirely (no deep merge), must have `version:1`.
* `Ui/BarWidget.qml` base injects `bar,moduleName,settings`; helpers `broadcast(method)`, `setting(name,fallback)`; geometry `vertical,barSize`.
* Bar commands: `omarchy bar use|reset|defaults|position|transparent|put|move|set`. Layout sections left/center/right.
* Background plugin uses bottom-layer `PanelWindow`; pattern for burn layer is click-through `mask: Region{}` + `WlrLayershell` bottom layer.
* Lock uses ext-session-lock + PAM; theme it, do not reimplement auth.
* Notifications: `popupModel`, history dir, DND persisted, durations low 5s / normal 8s / max 30s, top-right with bar clearance. Theme via `notifications.*` + card styling.

## Telemetry sources (no polling abuse)
* Battery: `UPower` via `services/battery/Service.qml`, 30s check, threshold 10.
* Power panel: `omarchy-battery-status --shell`, `omarchy-powerprofiles-list`, `omarchy-system-stats`.
* Network/audio/bluetooth: stock panels own NM/PipeWire/BlueZ; v2 prop reads same singletons read-only, never takes ownership.
* Workspace/window: `hyprctl` JSON where needed, throttled.

## Microcopy inventory (initial)
* `panels/power/Panel.qml:96-117`: `chargingPhrases=[Pumping power, Injecting electrons, Pouring juice, Amassing watts, Hoarding joules, Sucking volts, Topping reserves, Soaking amps, Inhaling kilowatts]`, `onBatteryPhrases=[Slurping power, Spending joules, Draining watts, Burning electrons, Sipping juice, ...]`, hero `Fully charged`.
* Full audit still open: clock, workspaces, network, bluetooth, audio, volume/brightness OSD, updates, weather, tray, agents, indicators, menus, dialogs, tooltips, errors. See `vocab/microcopy.md`.

## Decisions locked
* Fresh repo `omarchy-cogitator-v2`, old untouched.
* Green phosphor first.
* Prototype = prop + bar + burn (+ terminal theme).
* Font = investigate new OFL gothic-industrial monospace; keep JetBrainsMono Nerd Font as fallback.
