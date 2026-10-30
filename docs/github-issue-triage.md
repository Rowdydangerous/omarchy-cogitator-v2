# GitHub issue triage

Local fixes and remaining verification for issues #1–#3. No issues have been
closed, and these notes are not a claim of reporter-side live confirmation.

## #1 — delayed theme application

The CLI intentionally queues a detached transition: its return does not mean
the transition has completed. The control worker records completion only after
the transition command returns. Several minutes of stale color after completion
is **not** intentional.

The native theme command updates shell colors through IPC, then runs terminal
and application retint hooks. Local transition logs show one enable taking
about 22 seconds, including third-party hook errors; they do not reproduce the
reported 3–5 minute delay. Those unrelated hooks have not been modified.

The Node watcher correction in #2 addresses one concrete stale-palette risk,
but it does not prove the cause of stale Foot or bar colors. Still needed from
the affected system: Omarchy version, Cogitator commit, `cogitator status --json`,
and `journalctl --user -u cogitator-v2-transition --no-pager` covering an affected
enable, with observation times and whether the worker says completed. Redact
private paths or hook output before sharing. Do not add shell restarts or
rewrite terminal configuration speculatively.

## #2 — Node palette and teardown

The desktop **COGITATOR NODE** belongs to `cogitator-rite`; it is distinct from
the deliberately persistent **Control Sanctum** widget (`cogitator.control`)
beside the clock. Disable must stop the Node and its workspace CHANNEL OSD,
while retaining the control widget so the suite can be re-enabled.

Corrections:

- Periodically reopen the current palette file as well as watching it. Omarchy
  replaces the whole theme directory, which can invalidate a file-only watch.
  Ignore incomplete reads during replacement rather than resetting to green.
- On suite restoration, remove the coordinator even when an older native
  installation had already included it in the captured baseline. Keep the
  original baseline in recovery backups and preserve unrelated engaged edits.
- With no engagement journal, disable also stops a marked, still-enabled
  coordinator rather than only repairing legacy menu clones.

Fixture tests cover both clean and edited historical coordinator baselines,
the retained controller, and normal byte-identical restoration. The watcher
fix has now been deployed locally: `omarchy-shell cogitator-rite paletteStatus`
reports Amber's exact `#e8a33d` phosphor, `#ffd97a` bright, `#7a5a26` dim, and
`#060402` background. Live palette-switch and disable/re-enable confirmation
remain required before closing #2.

Deployment also exposed an independent `set -e` bug: when CRT or chamfers were
already disabled with no managed block present, their ensure functions returned
status 1 instead of a successful no-op. This silently aborted `cogitator apply`
before source deployment. Both now return success; a fixture checks the real
functions under `set -e` and confirms user configuration stays unchanged.

## #3 — global application and command search

The old custom Nexus filtered only ten generated root routes. Super+Space and
the coordinator's menu IPC now use the native menu lifecycle, which resolves
to the already-themed stock-derived `cogitator.menu` while engaged. Its existing
global search covers apps, nested commands, aliases, providers, conditions,
and user JSONC extensions; no command list or shell-action logic is duplicated.

This deliberately uses the stock-derived menu layout with Cogitator frames and
vocabulary rather than the limited custom root overlay. The standalone
Application Cogitator remains available by `openLauncher` IPC. Router fixtures
cover both engaged and disengaged states. Live keyboard search should be
confirmed on the reporting machine before closing #3.

### Follow-up: Aether, Actual Budget, and Basecamp missing

Live diagnosis found the scoped menu API had a shell handle but **no appLibrary**.
Consequently the menu indexed zero applications even though Quickshell's native
DesktopEntries enumerated all three applications (93 raw entries in total).
Searching could still match static menu commands, giving the impression that
only some apps were indexed.

`scripts/menu-style.py` now stages a fallback to the host's native
`qs.services.AppLibrary`, instantiated only when the injected handle is absent.
This reuses native hidden-entry rules, indexing, icons, launch feedback, and
removal semantics without changing the stock source baseline or the installed
desktop files. When a handle is supplied, the fallback stays unloaded.

After local deployment the menu indexes 76 visible applications; read-only
`appSearchStatus` calls confirm that all three named applications appear in
both the app library and menu search index. Example:

```bash
omarchy-shell shell call omarchy.menu appSearchStatus '{"query":"actual budget"}'
```

This diagnostic requires the menu to have been loaded/opened. It does not
launch applications or change the search filter. `tests/menu.py` exercises the
actual staged library binding in a separate offscreen Quickshell process with
fixture desktop entries, verifying visible apps, NoDisplay/configured hides,
and reuse of a supplied handle. Final keyboard confirmation remains advisable.

### Follow-up: Enter opened another launcher instead of the selected app

The legacy `overlays/rowdy.menu/Menu.qml` override still intercepted app-result
activation and called `cogitator-rite openLauncher` without the selected ID.
Restored native inline activation: capture the selected desktop ID/name, close
the menu, and call `appLibrary.launch(id, label)`. The separate Apps-submenu
handoff is unchanged; selecting an actual app search result launches directly.

An isolated offscreen Quickshell regression test executes the actual overlay
activation function with a recording app-library stub. It verifies keyboard and
pointer app activation, menu dismissal, invalid-index handling, submenu/action
routing, and untouched dmenu return values. No real apps are launched by tests.
