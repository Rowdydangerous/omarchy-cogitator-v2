import QtQuick
import Quickshell
import Quickshell.Wayland
import "../fx"

// Application Cogitator: keyboard-first command console over the shared
// DesktopEntries index. Summoned via
// `omarchy-shell cogitator-rite openLauncher`. Modal while open: the full
// window takes input, scrim click or Esc dismisses. No stock keybindings
// are touched; users may bind the summon command themselves, e.g. in
// ~/.config/hypr/bindings.lua.
Item {
    id: root
    required property var service

    readonly property bool opened: service ? service.launcherOpened : false
    readonly property color phosphor: "#4fd06a"
    readonly property color bright: "#7dff9a"
    readonly property color pale: "#d2ffd9"
    readonly property color dim: "#2f5b38"
    readonly property string mono: "Monaspace Xenon Frozen, JetBrainsMono Nerd Font, monospace"

    property string query: ""
    property var results: []
    property int selected: 0

    function refresh() {
        if (!service) {
            results = []
            selected = 0
            return
        }
        results = service.searchApps(query)
        selected = Math.max(0, Math.min(selected, results.length - 1))
    }

    function moveSelection(delta) {
        if (results.length > 0)
            selected = (selected + delta + results.length) % results.length
    }

    function launchSelected() {
        if (selected >= 0 && selected < results.length)
            service.launchApp(results[selected])
    }

    onOpenedChanged: {
        if (opened) {
            query = ""
            selected = 0
            refresh()
        }
    }

    Connections {
        target: root.service
        function onAppsRevisionChanged() { if (root.opened) root.refresh() }
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
            WlrLayershell.namespace: "cogitator-launcher"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

            onVisibleChanged: {
                if (visible)
                    Qt.callLater(function() { queryInput.forceActiveFocus() })
            }

            Rectangle {
                anchors.fill: parent
                color: Qt.rgba(1 / 255, 3 / 255, 2 / 255, 0.55)
                MouseArea {
                    anchors.fill: parent
                    onClicked: root.service.launcherOpened = false
                }
            }

            Rectangle {
                id: card
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: Math.max(60, parent.height * 0.16)
                width: Math.min(560, parent.width - 48)
                height: cardColumn.implicitHeight + 32
                color: Qt.rgba(3 / 255, 7 / 255, 4 / 255, 0.97)
                border.color: root.phosphor
                border.width: 1

                MouseArea { anchors.fill: parent; onClicked: function(mouse) { mouse.accepted = true } }

                Column {
                    id: cardColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 16
                    spacing: 10

                    Text {
                        text: "APPLICATION COGITATOR // SEARCH NOOSPHERE"
                        color: root.phosphor
                        font.family: root.mono
                        font.pixelSize: 11
                        font.bold: true
                        font.letterSpacing: 2
                    }

                    Rectangle {
                        width: parent.width
                        height: 46
                        color: "#010302"
                        border.color: queryInput.activeFocus ? root.bright : root.dim
                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 10
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: ">"
                                color: root.phosphor
                                font.family: root.mono
                                font.pixelSize: 16
                                font.bold: true
                            }
                            TextInput {
                                id: queryInput
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width - 60
                                text: root.query
                                color: root.pale
                                selectionColor: root.dim
                                font.family: root.mono
                                font.pixelSize: 14
                                maximumLength: 80
                                onTextEdited: {
                                    root.query = text
                                    root.selected = 0
                                    root.refresh()
                                }
                                Keys.onUpPressed: function(event) { root.moveSelection(-1); event.accepted = true }
                                Keys.onDownPressed: function(event) { root.moveSelection(1); event.accepted = true }
                                Keys.onReturnPressed: function(event) { root.launchSelected(); event.accepted = true }
                                Keys.onEscapePressed: function(event) { root.service.launcherOpened = false; event.accepted = true }
                            }
                        }
                    }

                    Repeater {
                        model: root.results
                        Rectangle {
                            required property var modelData
                            required property int index
                            width: cardColumn.width
                            height: 48
                            color: index === root.selected ? Qt.rgba(root.phosphor.r, root.phosphor.g, root.phosphor.b, 0.12) : "transparent"
                            border.color: index === root.selected ? root.phosphor : "transparent"
                            Row {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                spacing: 12
                                Image {
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 28
                                    height: 28
                                    source: root.service.appIconSource(modelData)
                                    sourceSize.width: 28
                                    sourceSize.height: 28
                                    fillMode: Image.PreserveAspectFit
                                }
                                Column {
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: parent.width - 130
                                    spacing: 1
                                    Text {
                                        width: parent.width
                                        text: String(modelData.name || "")
                                        color: root.pale
                                        font.family: root.mono
                                        font.pixelSize: 11
                                        font.bold: true
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        width: parent.width
                                        text: String(modelData.comment || "")
                                        color: root.dim
                                        font.family: root.mono
                                        font.pixelSize: 9
                                        elide: Text.ElideRight
                                    }
                                }
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: index === root.selected ? "[ READY ]" : ""
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
                                onClicked: root.service.launchApp(modelData)
                            }
                        }
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "TYPE TO FILTER // UP-DOWN TO SELECT // ENTER TO EXECUTE // ESC TO WITHDRAW"
                        color: root.dim
                        font.family: root.mono
                        font.pixelSize: 8
                        font.letterSpacing: 1
                    }
                }

                Crt {
                    intensity: root.service ? root.service.crtIntensity : 0.25
                    animated: root.service ? root.service.animate : true
                    flicker: 0
                }
            }
        }
    }
}
