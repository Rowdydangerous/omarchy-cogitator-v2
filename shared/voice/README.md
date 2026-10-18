# Cogitator terminal vocabulary

The suite speaks as a restrained Adeptus Mechanicus terminal: terse headings,
clear directives, ritual language in statuses. This is interface copy, not a
rename of system commands or backend state.

## Sources

* `lexicon.json`: labels, prompts, actions, status descriptions and menu vocabulary.
* `phrases.json`: power/auxiliary-link/archive status litanies.
* `plugin-names.json`: display names in the native plugin/widget catalogue.
* `scripts/voice-style.py`: presentation-only deployment and QML JS lookup builder.
* `docs/voice-inventory.json`: source strings with locations and review contexts.

| Surface | Voice |
|---|---|
| Audio | Vox Array; Vox Transmission / Vox Acquisition |
| Network | Noospheric Links; Relay Gateway; Address-resolution Oracle |
| Bluetooth | Auxiliary Machine Links; Registered Auxilia |
| Power | Power Reserve; Motive-force Doctrine |
| Display | Optic Array; Lumen Output; Inscription Scale |
| Weather | Atmospheric Auspex; Atmospheric Prognosis |
| Agents | Logic-engine Ledger; Cogitation Allowances |
| Clipboard | Data Buffer |
| Notifications | Machine Herald |
| Tray | Auxiliary Relic Registry |
| Lock / authorization | Present Access Cipher; Verifying Seal; Seal Rejected |
| Confirm / cancel / delete | Affirm / Withdraw / Purge |

Compact power-profile buttons use Conservation, Equilibrium and Overdrive;
their actual values remain power-saver, balanced and performance.

## Behavioral contract

Translation is applied only to display bindings and audited status presentation.
Raw JS model files, command strings, routes, IPC targets, boolean predicates,
profile values and returned chooser selections remain unchanged. The compiled
lookup is copied into each installed plugin's `voice/` directory. Source stock
baselines remain available for comparison.

App/device/network names, file paths, song titles, dates, measurements, provider
brands and caller-supplied chooser data are preserved. Incoming notification
content is not rewritten. External error details are retained, with a rite-failed
prefix where the view presents an error field.

The stock menu displays themed labels while searching both raw names and rite
aliases. App and font provider rows and dmenu values are excluded. Search
breadcrumbs use the themed names. Command Nexus route IDs remain unchanged.

## Maintenance and verification

Edit these JSON files, then use `cogitator apply`. Deployment keeps the restore
journal intact and requires no theme switch.

`tests/voice.py` checks predicates/actions, live names and password text,
multiline bindings, status/profile lookup, menu search/selection contracts,
all 37 plugin manifests and unchanged model JS, and QML lint regressions.
Shared frame copies receive the same dialogue vocabulary.

The source inventory includes review candidates that are protocol tokens or
technical reference text, not all of which should be translated. Regenerate it
with `python3 scripts/voice-style.py inventory`; do not bulk-replace its contents.

Live review checked Vox Array, Auxiliary Machine Links, Power Reserve, the
presentation menu and a rite-alias search for “doctrine”. Power-profile labels
were shortened after the first visual pass to fit their compact controls.
The refreshed running shell reported no relevant QML errors. Authentication
text is covered by packaging/lint checks without initiating an authentication
request during the visual review.
