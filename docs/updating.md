# Updating Cogitator

## 1. Recommended: one update entry point

```bash
cogitator update
```

Or use **Control Sanctum → Overview → Update from GitHub**. Both queue the same
worker, report status in the control widget, and share the transition log:

```bash
journalctl --user -u cogitator-v2-transition -n 60 --no-pager
```

The updater downloads the official GitHub repository's `main` branch into a
separate managed source checkout at `~/.local/share/cogitator-v2/source/` (honoring
`XDG_DATA_HOME`). After successful installation the `cogitator` shim and control
backend point to that source. Existing source checkouts are not changed.

- Engaged: deploy the updated coordinator, replacement plugins, controller, and
  generated settings, with one shell restart. Palette and wallpaper stay selected.
- Disengaged: update the controller/shim without engaging the suite; suite code
  is deployed on the next enable.
- Theme assets are downloaded but active theme files are not reapplied during
  code deployment. Reselect the palette if an update changes its theme assets.
- Restore journals remain armed. Pre-deployment copies of settings, shell config,
  and journals are kept under `~/.local/state/cogitator-v2/backups/update-*/`.
- Local tracked edits, diverged branches, untracked-file collisions, foreign
  destinations, and edited runtime receipts are not reset, cleaned, or discarded.
  A refusal means inspect the named path and preserve your changes before retrying.

This updates trusted project code, not Omarchy itself. It requires GitHub network
access. Update status is retained if download or deployment fails. Deployment is
not an automatic rollback of every live file: inspect the retained recovery files
and logs if it fails partway through.

### Older installs: bootstrap once without uninstalling

If `cogitator update` is not recognized, get a fresh source checkout. Use a new
directory; if this example destination already exists, use option 2 instead or
choose another unused path.

```bash
mkdir -p "$HOME/Projects"
git clone https://github.com/Rowdydangerous/omarchy-cogitator-v2.git \
  "$HOME/Projects/omarchy-cogitator-update"
"$HOME/Projects/omarchy-cogitator-update/scripts/cogitator" install
cogitator update
```

`install` preserves existing settings and adds/updates the independent control
widget; it does not engage the suite. The first update migrates future updates
to the dedicated source checkout. Do not run the native plugin updater first:
pulling into generated coordinator QML can invalidate its deployment receipt.

## 2. Manual update for a separate source clone

From the original **source** clone (not a deployed runtime plugin directory):

```bash
git status
git pull --ff-only
./scripts/cogitator apply
```

Stop if Git reports local changes or a conflict. Do not use `reset --hard` or
`clean` as a shortcut. This is also the development workflow: `apply` deploys
that working tree rather than downloading GitHub's published version.

For a standalone Git-managed plugin, Omarchy normally offers
`omarchy plugin update cogitator-rite --yes`. That command alone is **not** a
full-suite updater and may conflict with the generated QML; prefer option 1.

## 3. Reinstall while retaining settings

Removal/reinstallation is a fallback, not a prerequisite for updating. First
restore the original shell before removing any plugin:

```bash
cogitator disable
```

**Wait for restoration to finish.** The control widget should report completed;
`cogitator status --json` should report `snapshot: false` and an inactive suite.
If restoration fails, stop and inspect the logs rather than removing the files
needed to recover it.

Then:

```bash
cogitator uninstall
omarchy plugin add https://github.com/Rowdydangerous/omarchy-cogitator-v2.git --yes
bash "$HOME/.config/omarchy/plugins/cogitator-rite/scripts/cogitator" install
cogitator update
```

Do **not** pass `--purge`; normal uninstall retains saved settings and recovery
data. After the update completes, engage through the controller or run
`cogitator enable` if desired. The full-suite uninstaller uses Omarchy's native
removal commands for its installed roots. Removing only `cogitator-rite` via
Omarchy does not clean up the replacement suite or restore the previous theme.
