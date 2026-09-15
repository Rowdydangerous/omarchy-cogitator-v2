# Microcopy — inventory + liturgical direction

Source of truth for every user-facing string we re-theme. Stock first, rite replacement second.
Coherent system, not one-off jokes. Hierarchy: NOTICE / ADVISORY / WARNING / CRITICAL / SYSTEM / AUSPEX / COMMAND.

## Battery (stock `panels/power`)
Stock: Pumping power, Injecting electrons, Pouring juice, Amassing watts, Hoarding joules, Sucking volts, Topping reserves, Soaking amps, Inhaling kilowatts / Slurping power, Spending joules, Draining watts, Burning electrons, Sipping juice / Fully charged / Charging / Discharging / Time left / Time to full / POWER PROFILE
Rite direction:
* Normal: POWER RESERVE 087% / AUXILIARY CELLS NOMINAL
* Charging: ENERGY REQUISITION ACTIVE / CHARGING BATTERIUM / POWER INTAKE ACCEPTED
* Low: WARNING POWER RESERVES DEPLETING / AUXILIARY POWER REQUIRED
* Critical: +++ CRITICAL POWER FAILURE IMMINENT +++ / NONESSENTIAL SYSTEMS TO BE PURGED

## Network
Stock: connected/disconnected, signal %, provider names (audit open).
Rite: NOOSPHERIC LINK ESTABLISHED / NOOSPHERE CONNECTION DEGRADED / DATA RELAY LOST

## Bluetooth
Rite: AUXILIARY MACHINE LINK ACTIVE

## Audio
Rite: AUSPEX AUDIO ARRAY ACTIVE

## Updates
Rite: SANCTIFICATION DATA AVAILABLE / MACHINE SPIRIT REQUIRES RITES OF MAINTENANCE

## Notifications
Rite: +++ LOW PRIORITY SYSTEM NOTICE +++ / +++ MACHINE SPIRIT ADVISORY +++ / +++ OPERATOR WARNING +++ / +++ CRITICAL SYSTEM ALERT +++

## Audit outcome (Phase 4)

Stock first-party strings (power panel "Spending joules" et al, clock
formats, OSD volume/brightness glyphs, weather labels, tray menus) live in
`$OMARCHY_PATH/shell` QML and cannot be rewritten from a third-party
service plugin — the shell only shares its curated AppLibrary with
`menu`-kind plugins, and claiming that kind registers a panel entry.
Verdict: leave stock strings untouched and themed; carry the liturgical
voice in our own surfaces (prop communiques, channel OSDs, launcher,
terminal rite, notifications we send). The single justified exception,
deferred to the shell-twin stretch goal: cloning `omarchy.power` for a
power-cell console.

## Still to audit
lock strings (visually unverified — tokens derived from renderer),
agents/indicators advanced states, dialog confirmations.
