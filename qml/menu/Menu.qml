import QtQuick
import Quickshell
import Quickshell.Wayland
import "../fx"
import "Routes.js" as Routes

// Cogitator command menu: grimdark front door over the stock menu routes.
// APPLICATIONS opens the internal Application Cogitator; every other rite
// delegates to the stock omarchy.menu at its route (panels stay stock).
// Summoned via `omarchy-shell cogitator-rite toggleMenu`. Stock keybindings
// are untouched; SUPER+SPACE routing lives in scripts/cogitator-menu.
Item {
    id: root
    required property var service

    readonly property bool opened: service ? service.menuOpened : false
    readonly property color phosphor: root.service ? root.service.phosphor : "#4fd06a"
    readonly property color bright: root.service ? root.service.bright : "#7dff9a"
    readonly property color pale: root.service ? root.service.pale : "#d2ffd9"
    readonly property color dim: root.service ? root.service.dim : "#2f5b38"
    readonly property color abyss: root.service ? root.service.abyss : "#030704"
    readonly property string mono: "Monaspace Xenon Frozen, JetBrainsMono Nerd Font, monospace"

    property int selected: 0
    readonly property var entries: Routes.routes

    function moveSelection(delta) {
        if (entries.length > 0)
            selected = (selected + delta + entries.length) % entries.length
    }

    function activateSelected() {
        if (selected < 0 || selected >= entries.length)
            return
        activateEntry(entries[selected])
    }

    function activateEntry(entry) {
        if (!entry || !service)
            return
        if (entry.internal)
            service.openLauncherFromMenu()
        else
            service.summonStockMenu(entry.id)
    }

    onOpenedChanged: {
        if (opened) {
            selected = 0
            Qt.callLater(function() { keyCatcher.forceActiveFocus() })
        }
    }

    Variants {
        model: Quickshell.screens

        PanelWindow {
            required property var modelData

            screen: modelData
            visible: root.opened
            anchors { top: true; bottom: true; left: true; right: true }
            color: "transparent"
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "cogitator-menu"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

            onVisibleChanged: {
                if (visible)
                    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
            }

            Rectangle {
                anchors.fill: parent
                color: Qt.rgba(root.abyss.r, root.abyss.g, root.abyss.b, 0.55)
                MouseArea {
                    anchors.fill: parent
                    onClicked: root.service.menuOpened = false
                }
            }

            Item {
                id: keyCatcher
                anchors.fill: parent
                focus: true
                Keys.onUpPressed: function(event) { root.moveSelection(-1); event.accepted = true }
                Keys.onDownPressed: function(event) { root.moveSelection(1); event.accepted = true }
                Keys.onReturnPressed: function(event) { root.activateSelected(); event.accepted = true }
                Keys.onEscapePressed: function(event) { root.service.menuOpened = false; event.accepted = true }
            }

            Rectangle {
                id: card
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: Math.max(60, parent.height * 0.16)
                width: Math.min(480, parent.width - 48)
                height: cardColumn.implicitHeight + 32
                color: Qt.rgba(root.abyss.r, root.abyss.g, root.abyss.b, 0.97)
                border.color: root.phosphor
                border.width: 1

                MouseArea { anchors.fill: parent; onClicked: function(mouse) { mouse.accepted = true } }

                Column {
                    id: cardColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 16
                    spacing: 4

                    Text {
                        text: "COMMAND NEXUS // SELECT RITE"
                        color: root.phosphor
                        font.family: root.mono
                        font.pixelSize: 11
                        font.bold: true
                        font.letterSpacing: 2
                    }

                    Repeater {
                        model: root.entries
                        Rectangle {
                            required property var modelData
                            required property int index
                            width: cardColumn.width
                            height: 44
                            color: index === root.selected ? Qt.rgba(root.phosphor.r, root.phosphor.g, root.phosphor.b, 0.12) : "transparent"
                            border.color: index === root.selected ? root.phosphor : "transparent"
                            Row {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                spacing: 12
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: modelData.index
                                    color: root.dim
                                    font.family: root.mono
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: modelData.icon
                                    color: index === root.selected ? root.bright : root.phosphor
                                    font.pixelSize: 16
                                }
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: modelData.label.toUpperCase()
                                    color: index === root.selected ? root.pale : root.phosphor
                                    font.family: root.mono
                                    font.pixelSize: 12
                                    font.bold: index === root.selected
                                    font.letterSpacing: 1
                                }
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: index === root.selected ? (modelData.internal ? "[ ENTER ]" : "[ OPEN ]") : ""
                                    color: root.bright
                                    font.family: root.mono
                                    font.pixelSize: 9
                                    font.bold: true
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: root.selected = index
                                onClicked: root.activateEntry(modelData)
                            }
                        }
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "UP-DOWN TO SELECT // ENTER TO COMMIT RITE // ESC TO WITHDRAW"
                        color: root.dim
                        font.family: root.mono
                        font.pixelSize: 8
                        font.letterSpacing: 1
                    }
                }

                Crt {
                    intensity: root.service ? root.service.crtIntensity : 0.25
                    animated: root.service ? root.service.animate : true
                    fullMotion: root.service ? root.service.animationLevel === "full" : true
                    flicker: 0
                    noise: root.service ? root.service.noise : 0.03
                    falloff: root.service ? root.service.brightnessFalloff : true
                    grain: root.bright
                    soft: root.service && root.service.crtGlobal ? 0.35 : 1.0
                }
            }
        }
    }
}
