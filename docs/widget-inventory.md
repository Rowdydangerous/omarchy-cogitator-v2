# Widget and plugin inventory

All entries below are imported under `plugins/<name>/`, with replacement ID
`cogitator.<name>`. Most are **stock-baseline**; the bar has a small clone API
compatibility adapter. Enable installs all roots and activates the components
already enabled in the user's configuration.
Exact imported release, manifests and file hashes are in `stock-baseline.json`.

| Category | Plugin directories | Review focus |
|---|---|---|
| Bar engine | `bar` | Geometry, widget loading, popups, orientation, drag layout |
| Simple widgets | `active-window`, `workspaces`, `keyboard-layout`, `microphone`, `system-update`, `tray`, `indicators`, `spacer` | Labels, interactions, tooltips, indicators and multiple instances |
| Rich widgets | `agents`, `audio`, `bluetooth`, `clock`, `dropbox`, `monitor`, `network`, `power`, `tailscale`, `weather` | Popup geometry and all existing controls |
| Media | `media` | Service plus widget; playback and cover-art popup |
| Menus/overlays | `menu`, `clipboard`, `emojis`, `image-picker`, `reminders` | Keyboard navigation, filtering, selection round trips |
| Utility panels | `osd`, `disk-speedtest`, `speedtest`, `wifiqr` | IPC routing, progress/state presentation |
| Visual services | `background`, `notifications` | Layer order, notification actions, DND and history |
| Operational services | `battery`, `idle`, `nightlight` | Preserve behavior; little or no visual styling |
| Authentication surfaces | `lock`, `polkit` | Presentation only; preserve session lock and authentication |
| Development | `dev-gallery` | Reference preview surface; do not auto-enable |

## Existing Cogitator components

| Path | Used today? | Purpose |
|---|---|---|
| `qml/Service.qml` | Yes, while engaged | Telemetry, configuration, palette following and IPC |
| `qml/prop/` | Configurable | Persistent telemetry console behind windows |
| `qml/burn/` | Configurable | Click-through static burn layer |
| `qml/fx/` | Configurable | Local CRT treatment |
| `qml/menu/` | Yes | Custom Command Nexus and route definitions |
| `qml/launcher/` | Yes | Custom application search and launch |
| `overlays/rowdy.menu/` | Yes | Styled menu clone and launcher handoff |
| `overlays/notifications/` | Yes | Styled notification card |
| `hypr/crt.frag.tpl` | Configurable | Generated global compositor shader |
| `palettes/` | Yes | Color definitions and theme renderer |
| Root theme files / `themes/` | Yes | Native theme outputs, including alternate palettes |
| `extras/bash/` | Only when manually sourced | Optional Bash prompt; not a widget |
| `docs/reference/` | Documentation only | Font research and proposed machine vocabulary |
| `plugins/` | Enabled components only | Complete stock-based sources deployed by enable/apply |

## Activation findings

Native clone enablement preserves a source widget's settings when replacing its
layout entry, but it operates on a single found entry. The suite must explicitly
handle multiple instances (notably Indicators and Spacer), and remap the clock
center anchor when IDs change.

Existing custom clones need an explicit preservation strategy: `clonedFrom`
routing may select an enabled clone, so installing a second active replacement
for the same source is not sufficient. The suite must select one active route
and retain the original clone files and state for rollback.

The present full-bar copy contains stock widget manifests as support files.
Install only the individual plugin root intended for discovery; do not treat
every embedded manifest as another suite plugin.
