# Interactive Auspex console

The side console remains on the desktop's bottom layer: applications cover it,
it reserves no workspace space, and it never takes keyboard focus. Only its own
frame receives pointer input. No shortcuts, monitor settings, authentication, or
hardware-control logic are changed.

## Inspect a readout

Hover a row for its action hint, then click:

| Readout | Action |
| --- | --- |
| Logic engine / memory vault | Open or focus `btop` through Omarchy's TUI launcher |
| Home vault | Open Files |
| Power | Open the existing power panel |
| Chrono | Open the existing clock/calendar panel |
| Channel | Open Control Sanctum's Surfaces page |
| Net link | Open the existing network panel |
| Vox array | Open the existing audio panel |
| Relay | Open the existing Bluetooth panel |

The footer also provides Processes, Files, and Control buttons. Native panel
summoning respects the user's enabled widgets; the console does not enable a
disabled widget or change a hardware setting itself. An unavailable control or
failed command is recorded as an inspection warning.

Short screens can scroll the console; the observation log has its own scrollable
history. The footer sits at the bottom on taller screens rather than leaving a
large unstructured blank area.

## Machine communique

The **observation log stays factual**. The machine-spirit stream gives the same
events a little personality—for example, a real high-load event can say “THE
LOGIC ENGINES LABOUR,” while the log retains the measured percentage. It reacts to:

- Workspace selection, network/relay state changes, and audio mute/output state.
- External/battery power changes, 10% battery milestones, and low/critical conditions.
- High CPU or memory pressure and recovery (with hysteresis to avoid flapping).
- Low filesystem space, failed sampling, and restored sampling.

There are no periodic percentage recitations. During quiet, low-load periods,
an existing 45-second timer can offer one of the classics (“EXAMINING THE LATENT
MACHINE SPIRIT,” “PRAISING THE MACHINE GOD,” etc.). These are clearly personality,
not completed diagnostics, and **never create observation-log entries**. Idle
lines wait until events have settled and never appear during stale telemetry,
power/load/storage warnings, or a lost network link.

Messages normally finish before advancing. Warnings interrupt idle musings, and
critical messages take priority immediately. Normal commentary becomes factual
while battery power is critical. The queue keeps up to eight observations,
coalescing repeated event types and prioritizing serious events; the log keeps
the latest 32. Both are
session-local and reset when Quickshell restarts—no event history is written to
disk or sent anywhere. Frequent volume changes are not logged as separate events.
Battery milestones fire when reaching/crossing a 10% boundary in the expected
charge/discharge direction, not on every percent. Threshold jitter is suppressed;
a large drop produces one latest milestone, not a backlog. Low/critical warnings
replace redundant milestone chatter at 20%/10%.

## Change what the spirit says

Edit **`qml/prop/spirit-messages.json` in the project source**, then run
`./scripts/cogitator apply` to deploy it. Do not edit the receipted installed
runtime copy: the updater deliberately preserves/refuses direct runtime edits.

```json
"cpu.high": {
  "level": "warning",
  "log": "LOGIC ENGINE / HIGH LOAD {percent}%",
  "voice": ["THE LOGIC ENGINES LABOUR. / {percent}% LOAD."]
}
```

- `log` is the factual observation; `voice` is a list of commentary alternatives.
  Multiple alternatives cycle without an immediate repeat. Add/change these strings without
  touching telemetry code. `{percent}`, `{channel}`, `{state}`, `{status}`,
  `{boundary}`, and `{usage}` insert the corresponding real event values.
- The top-level `idle` list holds the classics. Those phrases never enter the log.
- Keep event IDs, severity levels, and relevant placeholders intact. Invalid JSON
  or incomplete catalogs retain the last valid catalog rather than breaking the
  console. Critical-battery severity cannot be downgraded by a catalog edit.

Formatting, pressure hysteresis, battery milestones, and queue policy are pure,
tested functions in `qml/prop/Spirit.js`; QML handles signal wiring and display.
No event adds a subprocess, remote call, or periodic poll. The catalog is read once
and watched for changes; typing sleeps between messages. Power changes use UPower
signals instead of once-per-second polling. Telemetry polling stops when the
console is disabled (not merely covered by another window).

## Reading controls

**Hold** pauses the communique, not telemetry or event collection. **Resume**
continues it. Text types at **70 ms per character** by default (about 14 characters
per second), followed by a reading pause. Multiple monitors share the same stream.

In **Control Sanctum → Surfaces**, adjust **Communique typing — ms per character**
(`STREAM_CHAR_INTERVAL`, 20–200; higher is slower). Turn off Text Streaming to show
messages immediately; minimal motion also disables typing. Existing settings
files receive the default without needing an automatic rewrite.

## Measured history, not decoration

A single small Python sampler reads `/proc/stat`, `/proc/meminfo`, `/proc/uptime`,
and filesystem capacity for the home filesystem every five seconds. It uses only
the Python standard library. It does not run `top`, enumerate process names, query
remote services, or need elevated privileges.

CPU usage comes from the difference between two counter readings. The first CPU
reading is unknown, not an invented zero. The two-minute CPU/memory plots retain
up to 24 timestamped samples and never pre-fill a fictional waveform. Missing
samples are not interpolated across long gaps; samples older than 15 seconds are
marked stale. Home-vault free space describes the filesystem containing the home
directory, not the size of that directory.

The read-only diagnostic `omarchy-shell cogitator-rite auspexStatus` reports sample
state, history/queue sizes, and the current typed message for troubleshooting.
