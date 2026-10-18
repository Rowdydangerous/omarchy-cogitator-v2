# Stock-based Cogitator plugins

Each child directory is a complete replacement-plugin baseline. The root
manifest uses `cogitator.<name>` and records its stock source in
`omarchy.clonedFrom`; stock IPC targets inside the code are intentionally kept.

`cogitator enable` installs all roots and activates replacements only for
components already enabled in your configuration. `cogitator apply` deploys
working-tree changes while retaining the original restore journal. The menu
and notification overlays are applied to their staged plugin copies.
See `../docs/suite-switching.md` for lifecycle details and
`../docs/stock-baseline.json` for upstream provenance.

The bar has a small compatibility adapter forwarding its approved narrow
service proxies to child widgets. Indicators uses a relocated dependency URL.
Neither changes stock authentication or service behavior.

Do not reimport over styled files. Compare a fresh upstream release in a
separate checkout, review its changes, and update the baseline record explicitly.
