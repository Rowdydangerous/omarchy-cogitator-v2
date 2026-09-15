import QtQuick
import Quickshell
import Quickshell.Wayland

// Background burn: phosphor afterimages behind windows.
// Fully click-through, very low opacity, drifts almost imperceptibly.
// Static frame when animation is minimal.
Item {
    id: root
    required property var service

    readonly property color phosphor: root.service ? root.service.phosphor : "#4fd06a"
    readonly property color dim: root.service ? root.service.dim : "#2f5b38"
    readonly property string mono: "Monaspace Xenon Frozen, JetBrainsMono Nerd Font, monospace"

    Variants {
        model: Quickshell.screens

        PanelWindow {
            required property var modelData

            screen: modelData
            visible: root.service.burnEnabled && root.service.burnOpacity > 0
            anchors { top: true; bottom: true; left: true; right: true }
            color: "transparent"
            exclusionMode: ExclusionMode.Ignore
            mask: Region {}
            WlrLayershell.namespace: "cogitator-burn"
            WlrLayershell.layer: WlrLayer.Bottom
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

            Item {
                anchors.fill: parent
                opacity: root.service.burnOpacity

                // Deliberately static: a full-screen drift forces a full
                // repaint every frame (~15% CPU). Motion lives in the prop
                // sweep and streaming text, which damage small regions.
                Item {
                    id: drift
                    anchors.fill: parent

                // Faint targeting grid.
                Repeater {
                    model: 12
                    Rectangle {
                        x: index * 180
                        y: 0
                        width: 1
                        height: parent.height
                        color: root.dim
                    }
                }
                Repeater {
                    model: 8
                    Rectangle {
                        x: 0
                        y: index * 150
                        width: parent.width + 120
                        height: 1
                        color: root.dim
                    }
                }

                // Ghost telemetry remnants.
                Text {
                    x: 90
                    y: 140
                    text: "NOOSPHERIC LINK ......... ESTABLISHED"
                    color: root.phosphor
                    font.family: root.mono
                    font.pixelSize: 13
                    font.letterSpacing: 3
                    opacity: 0.8
                }
                Text {
                    x: 90
                    y: 168
                    text: "DATA INTEGRITY .......... 99.7%"
                    color: root.phosphor
                    font.family: root.mono
                    font.pixelSize: 13
                    font.letterSpacing: 3
                    opacity: 0.6
                }
                Text {
                    x: parent.width - 560
                    y: parent.height - 180
                    text: "MACHINE SPIRIT .... STABLE"
                    color: root.phosphor
                    font.family: root.mono
                    font.pixelSize: 13
                    font.letterSpacing: 3
                    opacity: 0.55
                }
                Text {
                    x: 90
                    y: parent.height - 150
                    text: "SECTOR LOCAL // AUTHORITY OPERATOR // ACCESS SANCTIFIED"
                    color: root.phosphor
                    font.family: root.mono
                    font.pixelSize: 11
                    font.letterSpacing: 2
                    opacity: 0.45
                }

                // Faded warning glyph.
                Rectangle {
                    x: parent.width - 220
                    y: 120
                    width: 120
                    height: 120
                    radius: 60
                    color: "transparent"
                    border.color: root.dim
                    border.width: 2
                    Text {
                        anchors.centerIn: parent
                        text: "IX"
                        color: root.dim
                        font.family: root.mono
                        font.pixelSize: 40
                        font.bold: true
                    }
                }
                }
            }
        }
    }
}
