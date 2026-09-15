import QtQuick
import Quickshell
import Quickshell.Wayland
import "../fx"

Item {
    id: root
    required property var service

    readonly property color phosphor: "#4fd06a"
    readonly property color bright: "#7dff9a"
    readonly property color pale: "#d2ffd9"
    readonly property color dim: "#2f5b38"
    readonly property color warn: "#e0ad2f"
    readonly property color crit: "#ff5345"
    readonly property string mono: "Monaspace Xenon Frozen, JetBrainsMono Nerd Font, monospace"

    Variants {
        model: Quickshell.screens

        PanelWindow {
            id: window
            required property var modelData

            screen: modelData
            visible: root.service.propEnabled
            anchors { top: true; bottom: true; left: true; right: true }
            color: "transparent"
            exclusionMode: ExclusionMode.Ignore
            mask: Region { item: frame }
            WlrLayershell.namespace: "cogitator-prop"
            // Background shell element: below windows, above wallpaper.
            // Same layer as the burn window; same-layer stacking follows
            // creation order, so Burn is declared first in Service.qml.
            WlrLayershell.layer: WlrLayer.Bottom
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

            Item {
                id: frame
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.topMargin: 38
                anchors.bottomMargin: 12
                anchors.right: root.service.propPosition === "left" ? undefined : parent.right
                anchors.left: root.service.propPosition === "left" ? parent.left : undefined
                anchors.rightMargin: 12
                anchors.leftMargin: 12
                width: 320

                property string displayedRite: root.service.currentRite

                Rectangle {
                    anchors.fill: parent
                    color: Qt.rgba(3 / 255, 7 / 255, 4 / 255, root.service.propOpacity)
                    border.color: root.dim
                    border.width: 1
                }

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 5
                    color: "transparent"
                    border.color: Qt.rgba(root.phosphor.r, root.phosphor.g, root.phosphor.b, 0.35)
                    border.width: 1
                }

                // Scan sweep with persistence/ghosting echoes trailing behind it.
                Rectangle {
                    id: sweep
                    visible: root.service.crtEnabled && root.service.animate
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    y: 8
                    height: 2
                    color: Qt.rgba(root.phosphor.r, root.phosphor.g, root.phosphor.b, 0.18)
                    SequentialAnimation on y {
                        running: sweep.visible
                        loops: Animation.Infinite
                        NumberAnimation { to: frame.height - 12; duration: 9000; easing.type: Easing.Linear }
                        PauseAnimation { duration: 1500 }
                        NumberAnimation { to: 8; duration: 0 }
                    }
                }
                Rectangle {
                    visible: sweep.visible && root.service.ghosting > 0
                    anchors.left: sweep.left
                    anchors.right: sweep.right
                    y: sweep.y - 16
                    height: 2
                    color: Qt.rgba(root.phosphor.r, root.phosphor.g, root.phosphor.b, 0.05 + root.service.ghosting * 0.08)
                }
                Rectangle {
                    visible: sweep.visible && root.service.persistence > 0
                    anchors.left: sweep.left
                    anchors.right: sweep.right
                    y: sweep.y - 34
                    height: 6
                    color: Qt.rgba(root.phosphor.r, root.phosphor.g, root.phosphor.b, 0.02 + root.service.persistence * 0.04)
                }
                // Static burn-in watermark. Zero animation cost.
                Text {
                    visible: root.service.screenBurn
                    anchors.left: parent.left
                    anchors.bottom: parent.bottom
                    anchors.margins: 14
                    text: "SIGMA-IX // BLESSED PATTERN"
                    color: root.dim
                    opacity: 0.16
                    font.family: root.mono
                    font.pixelSize: 8
                    font.letterSpacing: 2
                }

                Column {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    Text {
                        text: "COGITATOR NODE // " + root.service.dateText
                        color: root.phosphor
                        font.family: root.mono
                        font.pixelSize: 11
                        font.bold: true
                        font.letterSpacing: 2
                    }
                    Rectangle { width: parent.width; height: 1; color: root.dim }

                    TelemetryRow { label: "LOGIC ENGINE"; value: root.service.cpuPercent + "%"; alert: root.service.cpuPercent >= 90 }
                    TelemetryRow { label: "MEMORY VAULT"; value: root.service.memText; alert: root.service.memPercent >= 90 }
                    TelemetryRow {
                        label: "POWER"
                        value: root.service.powerText
                        alert: root.service.powerLow
                        critical: root.service.powerCritical
                    }
                    TelemetryRow { label: "CHRONO"; value: root.service.timeText }
                    TelemetryRow { label: "CHANNEL"; value: root.service.channelText }
                    TelemetryRow { label: "NET LINK"; value: root.service.netText; alert: !root.service.netOk; critical: !root.service.netOk }
                    TelemetryRow { label: "VOX ARRAY"; value: root.service.voxText; alert: root.service.voxText === "MUTED" }
                    TelemetryRow { label: "RELAY"; value: root.service.relayText }

                    Rectangle { width: parent.width; height: 1; color: root.dim }

                    Text {
                        text: "MACHINE COMMUNIQUE"
                        color: root.dim
                        font.family: root.mono
                        font.pixelSize: 9
                        font.bold: true
                        font.letterSpacing: 2
                    }
                    Text {
                        width: parent.width
                        text: frame.displayedRite + (streamTimer.running ? "_" : "")
                        color: root.pale
                        font.family: root.mono
                        font.pixelSize: 12
                        font.bold: true
                        wrapMode: Text.Wrap
                    }

                    Item { width: 1; height: 4 }

                    Text {
                        text: "AUSPEX SWEEP ........ COMPLETE"
                        color: root.dim
                        font.family: root.mono
                        font.pixelSize: 9
                    }
                    Text {
                        text: "ACCESS .............. SANCTIFIED"
                        color: root.dim
                        font.family: root.mono
                        font.pixelSize: 9
                    }
                }

                Crt {
                    visible: root.service.crtEnabled
                    intensity: root.service.crtIntensity
                    animated: root.service.animate
                    fullMotion: root.service.animationLevel === "full"
                    flicker: root.service.flicker
                    noise: root.service.noise
                    falloff: root.service.brightnessFalloff
                }

                Timer {
                    id: streamTimer
                    interval: 18
                    repeat: true
                    running: frame.visible && root.service.textStreaming && root.service.animate
                        && frame.displayedRite.length < root.service.currentRite.length
                    onTriggered: frame.displayedRite = root.service.currentRite.substring(0, frame.displayedRite.length + 1)
                }

                Connections {
                    target: root.service
                    function onCurrentRiteChanged() {
                        if (root.service.textStreaming && root.service.animate)
                            frame.displayedRite = ""
                        else
                            frame.displayedRite = root.service.currentRite
                    }
                }
            }

            component TelemetryRow: Item {
                required property string label
                required property string value
                property bool alert: false
                property bool critical: false
                width: parent.width
                height: 20
                Text {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    text: parent.label
                    color: root.dim
                    font.family: root.mono
                    font.pixelSize: 9
                    font.bold: true
                    font.letterSpacing: 1
                }
                Text {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: parent.value
                    color: parent.critical ? root.crit : (parent.alert ? root.warn : root.bright)
                    font.family: root.mono
                    font.pixelSize: 11
                    font.bold: true
                }
            }
        }
    }
}
