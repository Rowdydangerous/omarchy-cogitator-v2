# Omarchy Cogitator v2 — Imperial Cogitator Shell

Fresh start. Old `omarchy-cogitator/` is archived and untouched.

Goal: **a 40K Cogitator that happens to run Linux** — cinematic green-phosphor machine interface on Omarchy 4.x / Quickshell, fully reversible from user-space only.

## Safety contract

* Only user locations are ever touched:
  * `~/.config/omarchy/themes/cogitator-green/`
  * `~/.config/omarchy/plugins/cogitator-rite/`
  * `~/.config/cogitator-v2/`
  * `~/.local/state/cogitator-v2/`
* Never edit `/usr/share/omarchy/`, never edit stock themes, never overwrite `shell.json` without timestamped backup.
* `cogitator enable` snapshots, `cogitator disable` restores, `cogitator uninstall` removes only what it installed.
* TTY recovery: `cogitator-v2 disable; omarchy theme set "Osaka Jade"; omarchy restart shell`.

## Current phase

Phase 3 shell expansion, live-verified (2026-09-14): workspace channel
rites with OSD, read-only net/vox/relay telemetry, Application Cogitator
launcher (`omarchy-shell cogitator-rite openLauncher`), themed critical
notifications, opt-in Bash rite. Full enable → disable → exact-restore
cycle re-proven after every addition. Screenshots in `docs/screenshots/`.

## Usage

```bash
./tests/test.sh          # 25 read-only checks, must all pass
cogitator status         # ~/.local/bin/cogitator shim, installed on enable
./scripts/cogitator enable    # snapshots, native-installs plugin+theme, queues detached transition
./scripts/cogitator disable   # disables plugin, restores previous theme + background
./scripts/cogitator apply     # re-render config.json from cogitator.conf + rescan
./scripts/cogitator configure # edit ~/.config/cogitator-v2/cogitator.conf
./scripts/cogitator uninstall # disable first, then `plugin remove` + `theme remove` (keeps config; --purge removes all)
```

Native equivalents (the script is a snapshot/restore wrapper around these):

```bash
omarchy plugin add https://github.com/Rowdydangerous/omarchy-cogitator-v2 --yes
omarchy plugin enable cogitator-rite
omarchy theme set cogitator-green
omarchy plugin disable cogitator-rite
```

Enable/disable queue a transient `cogitator-v2-transition` user unit and
return immediately — `omarchy theme set` restarts the shell and kills the
invoking terminal, so never chain commands after them in one invocation.
Poll with `status`, inspect with
`journalctl --user -u cogitator-v2-transition --no-pager`.
An abort message right after enable/disable means your shell died, not the
transaction; re-check `status` before doing anything.

Prototype scope (locked): prop + bar + burn, green phosphor, Xenon-first
font stack with clean fallback, no system font change.

## Global CRT (all windows)

`CRT_GLOBAL=true` (default) routes every window through a compositor
screen shader: static scanlines + vignette, rendered from
`hypr/crt.frag.tpl` with your `CRT_INTENSITY`. It darkens only, never
recolors, and costs ~1% compositor CPU idle because it is static —
Hyprland refuses `time` uniforms without disabling damage tracking
(entire frames re-rendered constantly), so flicker and grain stay in the
small-region QML overlays instead. While the global treatment is on, the
QML scanlines soften automatically to avoid doubling.

Managed as a marker-guarded `hl.config` block in
`~/.config/hypr/looknfeel.lua` (backed up before first edit, removed on
disable/uninstall). A foreign `screen_shader` is never clobbered — the
installer stands down with a message instead.

## Performance

Measured quickshell CPU, settled, i7-1165G7 integrated graphics:

| Tier | Cost | Motion |
|------|------|--------|
| `minimal` | ~4% (near stock) | frozen consoles, telemetry text still updates |
| `normal` | ~7% | stepped scan sweep + streaming text |
| `full` | ~10% | + flicker, grain, rite rotation |

Design rules that earned this: no full-screen tweens (a 120s background
drift cost ~15% alone — cut), stepped carriage motion at ~8fps instead of
60fps glides, damage-small-region overlays, event-driven bindings over
polling, 5s telemetry cadence. Set `ANIMATION_LEVEL` in `cogitator.conf`,
then `cogitator apply`.

## Stretch goal (pinned, not started)

A full Cogitator twin of every Omarchy shell surface with Mechanicus
treatment — see `docs/stretch-shell-twin.md`. The Application Cogitator
launcher is the reference implementation for that effort.

## Settings

```bash
cogitator configure   # opens ~/.config/cogitator-v2/cogitator.conf in $EDITOR;
                      # if you save changes it applies them automatically,
                      # otherwise the shell is left untouched
cogitator apply       # re-render + full shell restart (services need it)
cogitator status      # theme, palette, plugin, snapshot in one glance
```

Every tunable lives in that one file: palette, CRT intensity, phosphor
glow, scanlines, flicker, noise, persistence, ghosting, burn-in,
background burn + opacity, text streaming, workspace rites, prop opacity
and position, animation tier. QML never hardcodes color — all shell
surfaces follow the active theme file live.

## Palettes

```bash
cogitator palette amber       # warm amber CRT
cogitator palette red         # damage-control emergency terminal
cogitator palette industrial  # gunmetal, aged cream, brass
cogitator palette green       # back to phosphor green
```

Custom phosphor: set `CUSTOM_PHOSPHOR="#7CFF6B"` in the conf, then
`cogitator palette custom`. Scales derive automatically; bar, menus,
notifications, lock, launcher, prop, and burn all follow because every
surface reads the theme file. Definitions live in `palettes/*.json`,
rendered by `palettes/render.py` (green also ships at the repo root as
the native-installable flagship).

## Terminal rite (opt-in)

`cogitator enable` places `~/.config/cogitator-v2/bash/cogitator.bash` and
nothing else — it never edits startup files. To take the rite, add this line
yourself to the interactive Bash startup file of your choice:

```bash
[ -r ~/.config/cogitator-v2/bash/cogitator.bash ] && source ~/.config/cogitator-v2/bash/cogitator.bash
```

While engaged the prompt becomes a green `[NOOSPHERE::host]` authorization
line with a restrained machine-spirit utterance every 30 prompts; on disable
the original prompt returns by itself. `cogitator_rite_disable` removes the
hook entirely.

## Command menu (SUPER+SPACE while engaged)

`cogitator enable` routes SUPER+SPACE through `scripts/cogitator-menu`:
engaged it toggles the grimdark Command Nexus (stock root routes with
original icons, generated from stock data), disengaged it falls through to
the stock menu. Selecting APPLICATIONS opens the Application Cogitator;
every other rite delegates to the stock `omarchy.menu` at its route, so
system panels stay stock. Direct IPC also works:

```bash
omarchy-shell cogitator-rite toggleMenu    # root rites
omarchy-shell cogitator-rite openLauncher  # straight to applications
```

## Layout

The repo root is deliberately both a native plugin root and a native
theme root, so Omarchy's own installers accept it directly:

* `manifest.json` + `qml/` — plugin `cogitator-rite` (prop + burn service).
  `omarchy plugin add <url>` installs id `cogitator-rite` from any clone URL.
* `colors.toml` + `shell.toml` + `backgrounds/` + `icons.theme` — green
  phosphor theme, generated from `palettes/green.json` via
  `palettes/render.py`. `omarchy theme install <url>` works; the theme slug
  then derives from the repo name, while `scripts/cogitator` pins the
  curated slug `cogitator-green`.
* `palettes/` — centralized color definitions (single source of truth)
* `config/` — single `cogitator.conf` example → `config.json` for QML
* `vocab/` — microcopy inventory + liturgical replacements
* `scripts/cogitator` — lifecycle wrapper (snapshot/restore) around the
  native `omarchy plugin` / `omarchy theme` commands
* `fonts/NOTES.md` — font investigation log
