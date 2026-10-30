import QtQuick
import QtQuick.Controls as Controls
import Quickshell
import Quickshell.Wayland
import "../fx"

Item {
    id: root
    required property var service

    readonly property color phosphor: root.service ? root.service.phosphor : "#4fd06a"
    readonly property color bright: root.service ? root.service.bright : "#7dff9a"
    readonly property color pale: root.service ? root.service.pale : "#d2ffd9"
    readonly property color dim: root.service ? root.service.dim : "#2f5b38"
    readonly property color warn: root.service ? root.service.warn : "#e0ad2f"
    readonly property color crit: root.service ? root.service.crit : "#ff5345"
    readonly property color abyss: root.service ? root.service.abyss : "#030704"
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

                Rectangle {
                    anchors.fill: parent
                    color: Qt.rgba(root.abyss.r, root.abyss.g, root.abyss.b, root.service.propOpacity)
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

                // Scan sweep, stepped like a machine carriage: ~8fps damage-only
                // repaints instead of a 60fps tween. Persistence/ghosting
                // echoes trail behind it.
                Rectangle {
                    id: sweep
                    visible: window.visible && root.service.crtEnabled && root.service.animate
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    y: 8
                    height: 2
                    color: Qt.rgba(root.phosphor.r, root.phosphor.g, root.phosphor.b, 0.18)
                    Timer {
                        interval: 120
                        running: sweep.visible
                        repeat: true
                        onTriggered: {
                            var next = sweep.y + Math.max(2, (frame.height - 20) / 75)
                            sweep.y = next > frame.height - 12 ? 8 : next
                        }
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

                Flickable {
                    id: viewport
                    anchors.fill: parent
                    anchors.margins: 16
                    clip: true
                    contentWidth: width
                    contentHeight: stack.implicitHeight
                    boundsBehavior: Flickable.StopAtBounds
                    Controls.ScrollBar.vertical: Controls.ScrollBar {
                        policy: Controls.ScrollBar.AsNeeded
                        width: 3
                        contentItem: Rectangle { implicitWidth: 3; color: root.phosphor; opacity: 0.6 }
                    }
                    // Short displays scroll instead of hiding controls below
                    // the screen. No keyboard focus or space reservation.
                    Column {
                        id: stack
                        width: viewport.width
                        spacing: 12
                        Column {
                            id: instruments
                            width: parent.width
                            spacing: 8
                            Text {
                                text: "AUSPEX // " + root.service.dateText
                                color: root.phosphor
                                font.family: root.mono
                                font.pixelSize: 12
                                font.bold: true
                                font.letterSpacing: 2
                            }
                            Text {
                                text: "COGITATOR NODE / CHANNEL " + root.service.channelText
                                color: root.dim; font.family: root.mono; font.pixelSize: 9
                            }
                            Rectangle { width: parent.width; height: 1; color: root.dim }
                            Column {
                                width: parent.width
                                TelemetryRow { label: "LOGIC ENGINE"; value: root.service.cpuValid && root.service.statsFresh ? root.service.cpuPercent + "%" : "--"; alert: root.service.cpuBusy; action: "processes" }
                                TelemetryRow { label: "MEMORY VAULT"; value: root.service.memValid && root.service.statsFresh ? root.service.memText : "--"; alert: root.service.memoryBusy; action: "processes" }
                                TelemetryRow { label: "HOME VAULT"; value: root.service.diskValid && root.service.statsFresh ? root.service.diskText : "--"; alert: root.service.diskBusy; action: "files"; smallValue: true }
                                TelemetryRow { label: "POWER"; value: root.service.powerText; alert: root.service.powerLow; critical: root.service.powerCritical; action: "power" }
                                TelemetryRow { label: "CHRONO"; value: root.service.timeText; action: "clock" }
                                TelemetryRow { label: "CHANNEL"; value: root.service.channelText; action: "channels" }
                                TelemetryRow { label: "NET LINK"; value: root.service.netText; alert: !root.service.netOk; action: "network" }
                                TelemetryRow { label: "VOX ARRAY"; value: root.service.voxText; alert: root.service.voxText === "MUTED"; action: "audio" }
                                TelemetryRow { label: "RELAY"; value: root.service.relayText; action: "bluetooth" }
                            }
                            Rectangle { width: parent.width; height: 1; color: root.dim }
                            Row {
                                width: parent.width; spacing: 8
                                Text {
                                    width: parent.width - 58
                                    text: "MACHINE COMMUNIQUE"
                                    color: root.dim; font.family: root.mono; font.pixelSize: 9; font.bold: true
                                }
                                ConsoleAction {
                                    width: 50; height: 20
                                    label: root.service.streamPaused ? "RESUME" : "HOLD"
                                    onTriggered: root.service.streamPaused = !root.service.streamPaused
                                }
                            }
                            Item {
                                width: parent.width; height: 68
                                Text {
                                    width: parent.width
                                    text: root.service.displayedRite + (root.service.typingRite && !root.service.streamPaused ? "_" : "")
                                    color: root.service.currentRiteLevel === "critical" ? root.crit : (root.service.currentRiteLevel === "warning" ? root.warn : root.pale)
                                    font.family: root.mono; font.pixelSize: 12; font.bold: true
                                    wrapMode: Text.Wrap
                                }
                            }
                            Rectangle { width: parent.width; height: 1; color: root.dim }
                            Trend { width: parent.width; title: "LOGIC LOAD"; samples: root.service.cpuHistory; fresh: root.service.statsFresh && root.service.cpuValid; ink: root.phosphor; muted: root.dim }
                            Trend { width: parent.width; title: "MEMORY LOAD"; samples: root.service.memoryHistory; fresh: root.service.statsFresh && root.service.memValid; ink: root.bright; muted: root.dim }
                        }

                        Item {
                            id: ledger
                            width: parent.width
                            height: Math.max(120, viewport.height - instruments.implicitHeight - footer.implicitHeight - 24)
                            Rectangle { width: parent.width; height: 1; color: root.dim }
                            Text {
                                y: 9
                                text: "OBSERVATION LOG / " + root.service.events.length + " RECORDS"
                                color: root.dim; font.family: root.mono; font.pixelSize: 9; font.bold: true
                            }
                            // Quiet register lines fill unused ledger space,
                            // without pretending there are unobserved events.
                            Repeater {
                                model: Math.max(0, Math.floor((ledger.height - 32) / 36))
                                Rectangle { y: 32 + index * 36; width: ledger.width; height: 1; color: root.dim; opacity: 0.18 }
                            }
                            ListView {
                                anchors { left: parent.left; right: parent.right; top: parent.top; bottom: parent.bottom; topMargin: 30 }
                                clip: true
                                model: root.service.events
                                spacing: 7
                                boundsBehavior: Flickable.StopAtBounds
                                delegate: Column {
                                    required property var modelData
                                    width: ListView.view.width
                                    spacing: 3
                                    Text { text: modelData.time; color: root.dim; font.family: root.mono; font.pixelSize: 8 }
                                    Text {
                                        width: parent.width
                                        text: modelData.message
                                        color: modelData.level === "critical" ? root.crit : (modelData.level === "warning" ? root.warn : root.phosphor)
                                        font.family: root.mono; font.pixelSize: 9; wrapMode: Text.Wrap
                                    }
                                }
                            }
                        }

                        Column {
                            id: footer
                            width: parent.width; spacing: 8
                            Rectangle { width: parent.width; height: 1; color: root.dim }
                            Row {
                                width: parent.width; spacing: 6
                                ConsoleAction { width: (parent.width - 12) / 3; label: "PROCESSES"; onTriggered: root.service.inspect("processes") }
                                ConsoleAction { width: (parent.width - 12) / 3; label: "FILES"; onTriggered: root.service.inspect("files") }
                                ConsoleAction { width: (parent.width - 12) / 3; label: "CONTROL"; onTriggered: root.service.inspect("control") }
                            }
                            Text {
                                text: "UPTIME " + root.service.uptimeText + " / SAMPLE " + root.service.sampleAgeText
                                color: root.service.statsFresh ? root.dim : root.warn
                                font.family: root.mono; font.pixelSize: 8
                            }
                            Text { text: "CLICK READOUTS TO INSPECT"; color: root.dim; font.family: root.mono; font.pixelSize: 8; font.letterSpacing: 1 }
                        }
                    }
                }

                Crt {
                    visible: window.visible && root.service.crtEnabled
                    intensity: root.service.crtIntensity
                    animated: root.service.animate
                    fullMotion: root.service.animationLevel === "full"
                    flicker: root.service.flicker
                    noise: root.service.noise
                    falloff: root.service.brightnessFalloff
                    grain: root.bright
                    soft: root.service.crtGlobal ? 0.35 : 1.0
                }

            }

            component TelemetryRow: Item {
                id: row
                required property string label
                required property string value
                property bool alert: false
                property bool critical: false
                property string action: ""
                property bool smallValue: false
                width: parent.width
                height: 25
                Rectangle { anchors.fill: parent; color: root.phosphor; opacity: rowMouse.containsMouse ? 0.09 : 0 }
                Text {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    text: parent.label
                    color: rowMouse.containsMouse ? root.phosphor : root.dim
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
                    font.pixelSize: row.smallValue ? 9 : 11
                    font.bold: true
                }
                Controls.ToolTip.visible: rowMouse.containsMouse
                Controls.ToolTip.text: root.service.inspectionHint(row.action)
                MouseArea {
                    id: rowMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.service.inspect(row.action)
                }
            }

            component ConsoleAction: Rectangle {
                required property string label
                signal triggered()
                height: 24
                color: Qt.rgba(root.phosphor.r, root.phosphor.g, root.phosphor.b, actionMouse.containsMouse ? 0.18 : 0.05)
                border.color: root.dim
                Text {
                    anchors.centerIn: parent
                    text: parent.label
                    color: root.phosphor; font.family: root.mono; font.pixelSize: 8; font.bold: true
                }
                MouseArea {
                    id: actionMouse
                    anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: parent.triggered()
                }
            }
        }
    }
}
