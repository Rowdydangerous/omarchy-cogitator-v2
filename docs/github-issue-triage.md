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
