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
./tests/test.sh          # 17 read-only checks, must all pass
./scripts/cogitator status
./scripts/cogitator enable    # snapshots, native-installs plugin+theme, queues detached transition
./scripts/cogitator disable   # disables plugin, restores previous theme + background
./scripts/cogitator apply     # re-render config.json from cogitator.conf + rescan
./scripts/cogitator configure # edit ~/.config/cogitator-v2/cogitator.conf
./scripts/cogitator uninstall # disable first, then `plugin remove` + `theme remove` (keeps config; --purge removes all)
```

Native equivalents (the script is a snapshot/restore wrapper around these):

```bash
omarchy plugin add <repo-url> --yes   # installs plugin id cogitator-rite
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

## Launcher summon

The stock menu and its keybindings are untouched. To open the Application
Cogitator from a keybinding, bind this command yourself, e.g. in
`~/.config/hypr/bindings.lua`:

```bash
omarchy-shell cogitator-rite openLauncher
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
