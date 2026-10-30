import QtQuick
import Quickshell
import Quickshell.Bluetooth
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Networking
import Quickshell.Services.Pipewire
import Quickshell.Services.UPower
import "prop"
import "burn"
import "launcher"
import "menu"
import "prop/Auspex.js" as Auspex
import "prop/Spirit.js" as Spirit

Item {
    id: root

    property var shell: null

    // Central config (written by scripts/cogitator from cogitator.conf).
    property bool propEnabled: true
    property string propPosition: "right"
    property real propOpacity: 0.92
    property bool burnEnabled: true
    property real burnOpacity: 0.08
    property string animationLevel: "full" // full | normal | minimal
    property bool textStreaming: true
    property int streamCharInterval: 70
    property bool workspaceRites: true
    property bool crtEnabled: true
    property bool crtGlobal: true
    property real crtIntensity: 0.25
    property real flicker: 0.05
    property real noise: 0.03
    property real persistence: 0.15
    property real ghosting: 0.10
    property bool screenBurn: false
    property bool brightnessFalloff: true

    readonly property bool animate: animationLevel !== "minimal"

    // Live telemetry (real data only).
    property int cpuPercent: 0
    property string memText: "-- / --"
    property int memPercent: 0
    property bool cpuValid: false
    property bool memValid: false
    property var previousCpu: null
    property var cpuHistory: []
    property var memoryHistory: []
    property string diskText: "--"
    property int diskPercent: 0
    property bool diskValid: false
    property real uptimeSeconds: 0
    property double clockMs: Date.now()
    property double lastStatsAt: 0
    readonly property bool statsFresh: lastStatsAt > 0 && clockMs - lastStatsAt < 15000
    readonly property string uptimeText: lastStatsAt ? Auspex.duration(uptimeSeconds + Math.max(0, clockMs - lastStatsAt) / 1000) : "--"
    readonly property string sampleAgeText: lastStatsAt ? Math.max(0, Math.floor((clockMs - lastStatsAt) / 1000)) + "s AGO" : "WAITING"
    property bool observing: false
    property bool cpuBusy: false
    property bool memoryBusy: false
    property bool diskBusy: false
    property bool pollFailed: false
    property string powerSource: ""
    property string lastVoxState: ""
    property var batteryObservation: null
    property string powerText: "EXTERNAL SUPPLY"
    property bool powerLow: false
    property bool powerCritical: false
    property string timeText: "--:--:--"
    property string dateText: ""
    property string channelText: "--"
    property bool launcherOpened: false
    property bool menuOpened: false
    property int appsRevision: 0

    function openLauncherFromMenu() {
        launcherOpened = true
        menuOpened = false
    }

    // Delegates a stock menu route (style, setup, system, ...) to the
    // first-party menu, closing our overlay first so only one console
    // owns the screen.
    function summonStockMenu(route) {
        launcherOpened = false
        menuOpened = false
        Quickshell.execDetached(["omarchy-shell", "shell", "summon", "omarchy.menu",
            JSON.stringify({ menu: String(route || "root") })])
    }

    // Live phosphor: follows the active Omarchy theme so a palette switch
    // recolors every Cogitator surface without touching QML. Green defaults
    // hold until the theme file first loads.
    property color phosphor: "#4fd06a"
    property color bright: "#7dff9a"
    property color pale: "#d2ffd9"
    property color dim: "#2f5b38"
    property color crit: "#ff5345"
    property color warn: "#e0ad2f"
    property color abyss: "#030704"
    property color surface: "#0a140c"

    readonly property string themeColorsPath: home + "/.local/state/omarchy/current/theme/colors.toml"

    function themeColor(raw, key, fallback) {
        var match = String(raw || "").match(new RegExp("^\\s*" + key + "\\s*=\\s*\"([^\"]+)\"", "m"))
        return match ? match[1] : fallback
    }

    function applyThemeColors(raw) {
        // A read during the directory swap may briefly see no file/content.
        // Retain the last complete palette until the next successful reload.
        if (themeColor(raw, "background", "") === "")
            return
        phosphor = themeColor(raw, "accent", "#4fd06a")
        bright = themeColor(raw, "light_foreground", "#7dff9a")
        pale = themeColor(raw, "bright_foreground", "#d2ffd9")
        dim = themeColor(raw, "muted", "#2f5b38")
        crit = themeColor(raw, "red", "#ff5345")
        warn = themeColor(raw, "yellow", "#e0ad2f")
        abyss = themeColor(raw, "background", "#030704")
        surface = themeColor(raw, "lighter_background", "#0a140c")
    }

    // Own lightweight index over shared DesktopEntries. The shell only
    // hands its curated AppLibrary to menu-kind plugins; a service-kind
    // prop must not claim that kind (the host would load us as a panel).
    // Launch + icons follow the same native resolvers the stock menu uses.
    readonly property var desktopApps: DesktopEntries.applications ? DesktopEntries.applications.values : []

    function searchApps(query) {
        var needle = String(query || "").toLowerCase().trim()
        var scored = []
        for (var i = 0; i < desktopApps.length; i++) {
            var entry = desktopApps[i]
            if (!entry || entry.noDisplay === true)
                continue
            var name = String(entry.name || "")
            if (name === "")
                continue
            var score = -1
            if (needle === "") {
                score = 1000
            } else {
                var lower = name.toLowerCase()
                if (lower.indexOf(needle) === 0)
                    score = 0
                else if (lower.indexOf(needle) !== -1)
                    score = 1
                else if (String(entry.comment || "").toLowerCase().indexOf(needle) !== -1)
                    score = 2
            }
            if (score >= 0)
                scored.push({ entry: entry, score: score, name: name.toLowerCase(), id: String(entry.id || "") })
        }
        scored.sort(function(a, b) {
            if (a.score !== b.score)
                return a.score - b.score
            if (a.name < b.name)
                return -1
            if (a.name > b.name)
                return 1
            return a.id < b.id ? -1 : 1
        })
        var out = []
        for (var j = 0; j < scored.length && j < 6; j++)
            out.push(scored[j].entry)
        return out
    }

    function appIconSource(entry) {
        var icon = entry ? String(entry.icon || "") : ""
        if (icon === "")
            return Quickshell.iconPath("application-x-executable", true)
        if (icon.indexOf("/") !== -1)
            return icon.charAt(0) === "/" ? "file://" + icon : icon
        var themed = Quickshell.iconPath(icon, true)
        return themed !== "" ? themed : Quickshell.iconPath("application-x-executable", true)
    }

    function launchApp(entry) {
        var id = entry ? String(entry.id || "") : ""
        if (id === "")
            return
        launcherOpened = false
        Quickshell.execDetached(["uwsm-app", "--", "gtk-launch", id + ".desktop"])
    }

    // Read-only bindings over shared system singletons. Never mutated here;
    // the stock panels retain full ownership of hardware control.
    readonly property var networkDevices: Networking.devices ? Networking.devices.values : []
    readonly property var audioSink: Pipewire.defaultAudioSink
    readonly property var btAdapter: Bluetooth.defaultAdapter
    readonly property var btDevices: Bluetooth.devices ? Bluetooth.devices.values : []

    readonly property string netText: {
        var wired = null
        var wifi = null
        for (var i = 0; i < networkDevices.length; i++) {
            var device = networkDevices[i]
            if (!device || !device.connected)
                continue
            if (device.type === DeviceType.Wired)
                wired = device
            else if (device.type === DeviceType.Wifi && !wifi)
                wifi = device
        }
        if (wired)
            return "HARDLINE"
        if (wifi) {
            var ssid = connectedWifiSsid(wifi)
            return ssid === "" ? "WIRELESS" : ssid.toUpperCase().substring(0, 14)
        }
        return "RELAY LOST"
    }
    readonly property bool netOk: netText !== "RELAY LOST"

    readonly property string voxText: {
        if (!audioSink || !audioSink.audio)
            return "NO OUTPUT"
        if (audioSink.audio.muted)
            return "MUTED"
        return String(Math.round(audioSink.audio.volume * 100)).padStart(3, "0") + "%"
    }

    readonly property string relayText: {
        if (!btAdapter)
            return "NO RELAY"
        if (!btAdapter.enabled)
            return "DORMANT"
        var linked = 0
        for (var i = 0; i < btDevices.length; i++) {
            if (btDevices[i] && btDevices[i].connected)
                linked++
        }
        return linked > 0 ? linked + " LINKED" : "IDLE"
    }

    function connectedWifiSsid(wifiDevice) {
        if (!wifiDevice || !wifiDevice.networks)
            return ""
        var networks = wifiDevice.networks.values
        for (var i = 0; i < networks.length; i++) {
            if (networks[i] && networks[i].connected)
                return String(networks[i].ssid || "")
        }
        return ""
    }

    function refreshChannel() {
        var focused = Hyprland.focusedWorkspace
        channelText = focused ? String(focused.id).padStart(2, "0") : "--"
    }

    function channelRite() {
        var before = channelText
        refreshChannel()
        if (before === channelText || channelText === "--")
            return
        reportEvent("workspace.selected", {channel: channelText})
        if (workspaceRites)
            osdRite("+++ CHANNEL " + channelText + " +++", "◈")
    }

    function osdRite(message, icon) {
        if (animationLevel === "minimal")
            return
        Quickshell.execDetached(["omarchy-shell", "osd", "show", JSON.stringify({
            icon: icon || "",
            message: message,
            duration: 1400
        })])
    }

    // Session-local, bounded observation ledger. No fake health checks, logs
    // written to disk, or notification spam. Messages finish before advancing.
    property var events: []
    property var pendingRites: []
    property int riteCursor: 0
    property var messageCatalog: null
    property var voiceCounters: ({})
    property var deferredEvents: []
    property double lastSpiritEventAt: 0
    property string currentRiteKind: "event"
    property string currentRite: ""
    property string displayedRite: ""
    property string currentRiteLevel: "normal"
    property bool streamPaused: false
    readonly property bool typingRite: textStreaming && animate && displayedRite.length < currentRite.length

    function loadSpirit(raw) {
        var catalog
        try { catalog = JSON.parse(raw) } catch (e) { console.warn("Invalid spirit message JSON; previous catalog retained"); return }
        if (!Spirit.validCatalog(catalog)) { console.warn("Invalid spirit message catalog; previous catalog retained"); return }
        messageCatalog = catalog
        var waiting = deferredEvents
        deferredEvents = []
        for (var i = 0; i < waiting.length; i++) reportEvent(waiting[i].id, waiting[i].values)
    }

    function reportEvent(id, values) {
        if (!observing) return
        if (!messageCatalog) { deferredEvents = deferredEvents.concat([{id: id, values: values || {}}]).slice(-8); return }
        var sequence = voiceCounters[id] || 0
        var entry = Spirit.message(messageCatalog, id, values || {}, sequence)
        if (!entry) { console.warn("Unknown spirit event: " + id); return }
        if (powerCritical && entry.level === "normal") entry.voice = entry.message
        voiceCounters[id] = sequence + 1
        postEvent(entry.message, entry.level, entry.voice, id)
    }

    function postEvent(message, level, voice, id) {
        if (!observing) return
        var now = Date.now()
        if (events.length && events[0].message === message && now - events[0].stamp < 30000) return
        var entry = {id: id || "", message: message, voice: voice || message,
                     kind: "event", level: level || "normal", stamp: now,
                     time: Qt.formatTime(new Date(now), "HH:mm:ss")}
        events = [entry].concat(events).slice(0, 32)
        lastSpiritEventAt = now
        pendingRites = Spirit.enqueue(pendingRites, entry)
        if (entry.level === "critical" && currentRiteLevel !== "critical"
            || entry.level === "warning" && currentRiteKind === "idle") riteHold.stop()
        if (!riteHold.running && !streamPaused) advanceRite()
    }

    function advanceRite() {
        if (!propEnabled || streamPaused || !pendingRites.length) return
        var next = pendingRites[0]
        pendingRites = pendingRites.slice(1)
        currentRiteLevel = next.level
        currentRiteKind = next.kind || "event"
        currentRite = next.voice || next.message
        displayedRite = textStreaming && animate ? "" : currentRite
        riteHold.restart()
    }

    onTextStreamingChanged: if (!textStreaming) displayedRite = currentRite
    onAnimateChanged: if (!animate) displayedRite = currentRite
    onPropEnabledChanged: {
        if (!observing) return
        if (!propEnabled) {
            previousCpu = null
            cpuValid = false
            riteHold.stop()
        } else if (typingRite) riteHold.restart()
        else advanceRite()
    }
    onStreamPausedChanged: {
        if (streamPaused) riteHold.stop()
        else if (typingRite) riteHold.restart()
        else advanceRite()
    }
    onStatsFreshChanged: {
        if (propEnabled && lastStatsAt > 0 && !statsFresh) reportEvent("telemetry.stale")
    }
    onNetTextChanged: reportEvent(netOk ? "network.up" : "network.down", {state: netText})
    onRelayTextChanged: reportEvent(relayText === "DORMANT" || relayText === "NO RELAY" ? "relay.quiet" : "relay.changed", {state: relayText})
    onVoxTextChanged: {
        var state = voxText === "MUTED" ? "muted" : (voxText === "NO OUTPUT" ? "missing" : "active")
        if (observing && lastVoxState && state !== lastVoxState)
            reportEvent("audio." + state)
        lastVoxState = state
    }

    function nextRite() {
        if (!messageCatalog || riteHold.running || !Spirit.canIdle({fresh: statsFresh,
            cpuValid: cpuValid, cpu: cpuPercent, warning: powerLow || cpuBusy || memoryBusy || diskBusy || !netOk || pollFailed,
            pending: pendingRites.length, typing: typingRite, paused: streamPaused, lastEvent: lastSpiritEventAt}, Date.now())) return
        var line = messageCatalog.idle[riteCursor++ % messageCatalog.idle.length]
        // Personality is not an observed event: never put idle liturgy in the log.
        pendingRites = [{voice: line, level: "normal", kind: "idle"}]
        advanceRite()
    }

    function updatePressure(metric, value) {
        var property = metric + "Busy"
        var transition = Spirit.pressure(root[property], metric, value)
        root[property] = transition.active
        if (transition.event) reportEvent(transition.event, {percent: value, usage: diskText})
    }

    function inspect(action) {
        var command = Auspex.actionCommand(action)
        if (!command.length || actionProc.running) return
        actionProc.command = command
        actionProc.running = true
    }

    function inspectionHint(action) { return Auspex.actionHint(action) }

    function statsFailure() {
        if (!pollFailed) reportEvent("telemetry.failed")
        pollFailed = true
    }

    function applyConfig(obj) {
        if (!obj || typeof obj !== "object")
            return
        if (typeof obj.propEnabled === "boolean")
            propEnabled = obj.propEnabled
        if (typeof obj.propPosition === "string")
            propPosition = obj.propPosition
        if (typeof obj.propOpacity === "number")
            propOpacity = Math.min(1, Math.max(0.4, obj.propOpacity))
        if (typeof obj.burnEnabled === "boolean")
            burnEnabled = obj.burnEnabled
        if (typeof obj.burnOpacity === "number")
            burnOpacity = Math.min(0.3, Math.max(0, obj.burnOpacity))
        if (typeof obj.animationLevel === "string")
            animationLevel = obj.animationLevel
        if (typeof obj.textStreaming === "boolean")
            textStreaming = obj.textStreaming
        if (typeof obj.streamCharInterval === "number")
            streamCharInterval = Math.round(Math.min(200, Math.max(20, obj.streamCharInterval)))
        if (typeof obj.workspaceRites === "boolean")
            workspaceRites = obj.workspaceRites
        if (typeof obj.crtEnabled === "boolean")
            crtEnabled = obj.crtEnabled
        if (typeof obj.crtGlobal === "boolean")
            crtGlobal = obj.crtGlobal
        if (typeof obj.crtIntensity === "number")
            crtIntensity = Math.min(1, Math.max(0, obj.crtIntensity))
        if (typeof obj.flicker === "number")
            flicker = Math.min(0.3, Math.max(0, obj.flicker))
        if (typeof obj.noise === "number")
            noise = Math.min(0.3, Math.max(0, obj.noise))
        if (typeof obj.persistence === "number")
            persistence = Math.min(1, Math.max(0, obj.persistence))
        if (typeof obj.ghosting === "number")
            ghosting = Math.min(1, Math.max(0, obj.ghosting))
        if (typeof obj.screenBurn === "boolean")
            screenBurn = obj.screenBurn
        if (typeof obj.brightnessFalloff === "boolean")
            brightnessFalloff = obj.brightnessFalloff
    }

    function refreshPower() {
        var wasLow = powerLow
        var wasCritical = powerCritical
        var before = powerSource
        powerSource = UPower.onBattery ? "BATTERY" : "EXTERNAL SUPPLY"
        var d = UPower.displayDevice
        var milestone = {event: ""}
        var pct = null
        if (!d || !d.isPresent) {
            batteryObservation = null
            powerText = UPower.onBattery ? "BATTERY / NO CHARGE DATA" : "EXTERNAL SUPPLY"
            powerLow = false
            powerCritical = false
        } else {
            pct = Math.round(d.percentage * 100)
            if (!isFinite(pct) || pct < 0 || pct > 100) {
                batteryObservation = null
                powerText = "BATTERY / CHARGE UNAVAILABLE"
                return
            }
            milestone = Spirit.batteryStep(batteryObservation, pct, UPower.onBattery)
            batteryObservation = milestone.state
            var flow = UPower.onBattery ? "DRAIN" : "INTAKE"
            powerText = String(pct).padStart(3, "0") + "% " + flow
            powerLow = UPower.onBattery && pct <= 20
            powerCritical = UPower.onBattery && pct <= 10
        }
        if (before && before !== powerSource) reportEvent(UPower.onBattery ? "power.battery" : "power.external", {status: powerText})
        if (!wasCritical && powerCritical) reportEvent("battery.critical", {percent: pct})
        else if (!wasLow && powerLow) reportEvent("battery.low", {percent: pct})
        else if (wasLow && !powerLow && before === powerSource) reportEvent("battery.recovered")
        else if (milestone.event && !powerLow) reportEvent(milestone.event, {percent: pct, boundary: milestone.boundary})
    }

    function parseStats(raw) {
        var data
        try { data = JSON.parse(raw) } catch (e) { statsFailure(); return }
        if (!data || (!data.cpu && !data.memory)) { statsFailure(); return }
        var now = Date.now()
        var cpu = Auspex.cpuUsage(previousCpu, data.cpu)
        previousCpu = data.cpu
        cpuValid = cpu !== null && isFinite(cpu)
        if (cpuValid) {
            cpuPercent = cpu
            cpuHistory = Auspex.appendSample(cpuHistory, cpu, now)
            updatePressure("cpu", cpu)
        }
        memValid = !!data.memory && isFinite(data.memory.percent)
        if (memValid) {
            memPercent = Math.max(0, Math.min(100, data.memory.percent))
            memText = data.memory.text
            memoryHistory = Auspex.appendSample(memoryHistory, memPercent, now)
            updatePressure("memory", memPercent)
        }
        diskValid = !!data.disk && isFinite(data.disk.percent)
        if (diskValid) {
            diskPercent = data.disk.percent
            diskText = diskPercent + "% USED / " + data.disk.freeGiB + " GiB FREE"
            updatePressure("disk", diskPercent)
        }
        if (isFinite(data.uptime) && data.uptime !== null) uptimeSeconds = data.uptime
        if (pollFailed) reportEvent("telemetry.restored")
        pollFailed = false
        lastStatsAt = now
    }

    readonly property string home: Quickshell.env("HOME")
    readonly property string configJsonPath: home + "/.config/cogitator-v2/config.json"

    FileView {
        path: Qt.resolvedUrl("prop/spirit-messages.json")
        watchChanges: true
        printErrors: true
        onLoaded: root.loadSpirit(text())
        onFileChanged: reload()
    }

    FileView {
        path: root.configJsonPath
        watchChanges: true
        printErrors: false
        onLoaded: {
            try {
                root.applyConfig(JSON.parse(text()))
            } catch (e) {}
        }
        onFileChanged: reload()
    }

    FileView {
        id: themeColorsFile
        path: root.themeColorsPath
        watchChanges: true
        printErrors: false
        onLoaded: root.applyThemeColors(text())
        onFileChanged: reload()
    }

    // Theme selection replaces the containing directory, not just this file.
    // A file-only watch can remain attached to the removed inode. Reopen the
    // path periodically as well so the Node cannot retain an old palette.
    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: themeColorsFile.reload()
    }

    Process {
        id: statsProc
        command: ["python3", decodeURIComponent(Qt.resolvedUrl("prop/stats.py").toString().replace(/^file:\/\//, ""))]
        onExited: function(exitCode) { if (exitCode !== 0) root.statsFailure() }
        stdout: StdioCollector {
            waitForEnd: true
            onStreamFinished: root.parseStats(text)
        }
    }

    Process {
        id: actionProc
        onExited: function(exitCode) { if (exitCode !== 0) root.reportEvent("inspection.failed") }
        stdout: StdioCollector {
            onStreamFinished: if (text.trim() === "unknown") root.reportEvent("inspection.unavailable")
        }
    }

    Timer {
        id: riteHold
        interval: Math.max(7000, root.currentRite.length * root.streamCharInterval + 3500)
        running: false
        onTriggered: root.advanceRite()
    }
    Timer {
        interval: root.streamCharInterval
        running: root.propEnabled && root.typingRite && !root.streamPaused
        repeat: true
        onTriggered: root.displayedRite = root.currentRite.substring(0, root.displayedRite.length + 1)
    }

    Timer {
        interval: 5000
        running: root.propEnabled
        repeat: true
        triggeredOnStart: true
        onTriggered: if (!statsProc.running) statsProc.running = true
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            var now = new Date()
            root.clockMs = now.getTime()
            root.timeText = Qt.formatTime(now, "HH:mm:ss")
            root.dateText = Qt.formatDate(now, "yyyy-MM-dd")
        }
    }

    Timer {
        interval: 45000
        running: root.textStreaming && root.propEnabled
        repeat: true
        onTriggered: root.nextRite()
    }

    Connections {
        target: UPower
        function onOnBatteryChanged() { root.refreshPower() }
    }

    Connections {
        target: UPower.displayDevice
        function onPercentageChanged() { root.refreshPower() }
        function onIsPresentChanged() { root.refreshPower() }
    }

    Connections {
        target: Hyprland
        function onFocusedWorkspaceChanged() { root.channelRite() }
    }

    Connections {
        target: DesktopEntries.applications
        function onValuesChanged() { root.appsRevision++ }
    }

    Component.onCompleted: {
        root.refreshPower()
        root.refreshChannel()
        root.observing = true
        root.reportEvent("session.open")
        if (root.powerCritical && root.batteryObservation)
            root.reportEvent("battery.critical", {percent: root.batteryObservation.percent})
        else if (root.powerLow && root.batteryObservation)
            root.reportEvent("battery.low", {percent: root.batteryObservation.percent})
    }

    IpcHandler {
        target: "cogitator-rite"

        function auspexStatus(): string {
            return JSON.stringify({fresh: root.statsFresh, cpuValid: root.cpuValid,
                cpu: root.cpuPercent, memory: root.memText, disk: root.diskText,
                uptime: root.uptimeText, cpuSamples: root.cpuHistory.length,
                memorySamples: root.memoryHistory.length, events: root.events.length,
                pending: root.pendingRites.length, typingInterval: root.streamCharInterval,
                paused: root.streamPaused, catalogReady: !!root.messageCatalog,
                kind: root.currentRiteKind, typed: root.displayedRite, message: root.currentRite})
        }

        function paletteStatus(): string {
            return JSON.stringify({phosphor: String(root.phosphor),
                bright: String(root.bright), dim: String(root.dim),
                background: String(root.abyss)})
        }

        function openLauncher(): string {
            root.launcherOpened = true
            return "ok"
        }

        function toggleLauncher(): string {
            root.launcherOpened = !root.launcherOpened
            return "ok"
        }

        function closeLauncher(): string {
            root.launcherOpened = false
            return "ok"
        }

        function openMenu(): string {
            root.summonStockMenu("root")
            return "ok"
        }

        function closeMenu(): string {
            root.menuOpened = false
            Quickshell.execDetached(["omarchy-menu", "close"])
            return "ok"
        }

        function toggleMenu(): string {
            root.launcherOpened = false
            root.menuOpened = false
            Quickshell.execDetached(["omarchy-menu", "toggle"])
            return "ok"
        }
    }

    // Declaration order is load-bearing: both windows share WlrLayer.Bottom
    // and same-layer surfaces stack in creation order (first = bottom).
    Burn { service: root }
    Prop { service: root }
    Launcher { service: root }
    Menu { service: root }
}
