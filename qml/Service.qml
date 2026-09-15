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
    property bool workspaceRites: true
    property bool crtEnabled: true
    property real crtIntensity: 0.25
    property real flicker: 0.05

    readonly property bool animate: animationLevel !== "minimal"

    // Live telemetry (real data only).
    property int cpuPercent: 0
    property string memText: "-- / --"
    property int memPercent: 0
    property string powerText: "EXTERNAL SUPPLY"
    property bool powerLow: false
    property bool powerCritical: false
    property string timeText: "--:--:--"
    property string dateText: ""
    property string channelText: "--"

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
        currentRite = "CHANNEL " + channelText + " SYNCHRONIZED"
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

    // Rotating rite corpus (shuffle bag, no immediate repeats).
    readonly property var liturgy: [
        "PRAISING THE MACHINE GOD",
        "EXAMINING THE LATENT MACHINE SPIRIT",
        "COMMUNING WITH THE MACHINE SPIRIT",
        "COMMENCING THE LITANY OF COMPUTATION",
        "SUBMITTING A SACRED QUERY",
        "TRANSMITTING THE LITANY",
        "AWAITING THE OMNISSIAH'S REVELATION",
        "REQUESTING DIVINE COMPUTATION",
        "INVOKING THE RITE OF CALCULATION",
        "CONSULTING THE HIGHER COGITATOR",
        "STIRRING THE COGITATOR BANKS",
        "ATTUNING THE MACHINE SPIRIT",
        "INTERPRETING THE MACHINE'S OMENS",
        "CONSULTING THE ANCIENT DATA-VAULTS",
        "INSCRIBING THE SACRED DATA-SLATE",
        "PERFORMING AUSPEX UPON THE NOOSPHERE"
    ]
    property var riteOrder: []
    property int riteCursor: 0
    property string currentRite: "AWAITING THE OMNISSIAH'S REVELATION"

    function nextRite() {
        if (riteCursor >= riteOrder.length) {
            riteOrder = root.liturgy.slice()
            for (var i = riteOrder.length - 1; i > 0; i--) {
                var j = Math.floor(Math.random() * (i + 1))
                var tmp = riteOrder[i]
                riteOrder[i] = riteOrder[j]
                riteOrder[j] = tmp
            }
            riteCursor = 0
        }
        currentRite = riteOrder[riteCursor]
        riteCursor++
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
        if (typeof obj.workspaceRites === "boolean")
            workspaceRites = obj.workspaceRites
        if (typeof obj.crtEnabled === "boolean")
            crtEnabled = obj.crtEnabled
        if (typeof obj.crtIntensity === "number")
            crtIntensity = Math.min(1, Math.max(0, obj.crtIntensity))
        if (typeof obj.flicker === "number")
            flicker = Math.min(0.3, Math.max(0, obj.flicker))
    }

    function refreshPower() {
        var d = UPower.displayDevice
        if (!d || !d.isPresent) {
            powerText = "EXTERNAL SUPPLY"
            powerLow = false
            powerCritical = false
            return
        }
        var pct = Math.round((d.percentage || 0) * 100)
        var flow = UPower.onBattery ? "DRAIN" : "INTAKE"
        powerText = String(pct).padStart(3, "0") + "% " + flow
        powerLow = pct <= 20
        powerCritical = pct <= 10
    }

    function parseStats(raw) {
        var lines = String(raw || "").split("\n")
        for (var i = 0; i < lines.length; i++) {
            var parts = lines[i].split("\t")
            if (parts.length < 2)
                continue
            if (parts[0] === "cpu") {
                var cpu = parseInt(parts[1], 10)
                if (isFinite(cpu))
                    cpuPercent = Math.min(100, Math.max(0, cpu))
            } else if (parts[0] === "memory") {
                memText = parts[1].trim()
                var m = memText.match(/([0-9.]+)GB\s*\/\s*([0-9.]+)GB/)
                if (m)
                    memPercent = Math.round(100 * parseFloat(m[1]) / parseFloat(m[2]))
            }
        }
    }

    readonly property string home: Quickshell.env("HOME")
    readonly property string configJsonPath: home + "/.config/cogitator-v2/config.json"

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

    Process {
        id: statsProc
        command: ["omarchy-system-stats"]
        stdout: StdioCollector {
            waitForEnd: true
            onStreamFinished: root.parseStats(text)
        }
    }

    Timer {
        interval: 5000
        running: true
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
            root.timeText = Qt.formatTime(now, "HH:mm:ss")
            root.dateText = Qt.formatDate(now, "yyyy-MM-dd")
            root.refreshPower()
        }
    }

    Timer {
        interval: 7000
        running: root.textStreaming && root.animate
        repeat: true
        onTriggered: root.nextRite()
    }

    Connections {
        target: UPower
        function onOnBatteryChanged() { root.refreshPower() }
    }

    Connections {
        target: Hyprland
        function onFocusedWorkspaceChanged() { root.channelRite() }
    }

    Component.onCompleted: {
        root.nextRite()
        root.refreshPower()
        root.refreshChannel()
    }

    // Declaration order is load-bearing: both windows share WlrLayer.Bottom
    // and same-layer surfaces stack in creation order (first = bottom).
    Burn { service: root }
    Prop { service: root }
}
