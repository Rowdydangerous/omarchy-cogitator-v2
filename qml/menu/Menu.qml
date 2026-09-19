import QtQuick
import Quickshell
import Quickshell.Wayland
import QtQuick.Shapes
import "../fx"
import "Routes.js" as Routes

// Cogitator command menu: grimdark front door over the stock menu routes.
// Type to filter like the stock menu; Right arrow commits like Enter.
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
    readonly property real chamfer: 30

    property int selected: 0
    property string filter: ""
    readonly property var entries: Routes.routes

    function filteredEntries() {
        var needle = filter.toLowerCase()
        if (needle === "")
            return entries
        var out = []
        for (var i = 0; i < entries.length; i++) {
            var entry = entries[i]
            if (entry.label.toLowerCase().indexOf(needle) !== -1
                || entry.id.toLowerCase().indexOf(needle) !== -1)
                out.push(entry)
        }
        return out
    }

    function visibleEntries() {
        return filteredEntries()
    }

    function moveSelection(delta) {
        var list = visibleEntries()
        if (list.length > 0)
            selected = (selected + delta + list.length) % list.length
    }

    function activateSelected() {
        var list = visibleEntries()
        if (selected >= 0 && selected < list.length)
            activateEntry(list[selected])
    }

    function activateEntry(entry) {
        if (!entry || !service)
            return
        if (entry.internal)
            service.openLauncherFromMenu()
        else
            service.summonStockMenu(entry.id)
    }

    function appendFilter(text) {
        if (filter.length < 24) {
            filter += text
            selected = 0
        }
    }

    function backspaceFilter() {
        if (filter.length > 0) {
            filter = filter.substring(0, filter.length - 1)
            selected = 0
        }
    }

    onOpenedChanged: {
        if (opened) {
            selected = 0
            filter = ""
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
                Keys.onRightPressed: function(event) { root.activateSelected(); event.accepted = true }
                Keys.onEscapePressed: function(event) {
                    if (root.filter !== "") root.filter = ""
                    else root.service.menuOpened = false
                    event.accepted = true
                }
                Keys.onBackspacePressed: function(event) { root.backspaceFilter(); event.accepted = true }
                Keys.onPressed: function(event) {
                    if (event.text && event.text.length === 1 && event.text.charCodeAt(0) >= 32
                        && (event.modifiers === Qt.NoModifier || event.modifiers === Qt.ShiftModifier)) {
                        root.appendFilter(event.text)
                        event.accepted = true
                    }
                }
            }

            Rectangle {
                id: card
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: Math.max(60, parent.height * 0.16)
                width: Math.min(560, parent.width - 48)
                height: cardColumn.implicitHeight + 32
                color: Qt.rgba(root.abyss.r, root.abyss.g, root.abyss.b, 0.97)
                border.width: 0

                MouseArea { anchors.fill: parent; onClicked: function(mouse) { mouse.accepted = true } }

                // Chamfered frame: bottom-right corner cut at 45 degrees.
                Shape {
                    anchors.fill: parent
                    preferredRendererType: Shape.CurveRenderer
                    ShapePath {
                        strokeColor: root.phosphor
                        strokeWidth: 2
                        fillColor: "transparent"
                        PathMove { x: 0; y: 0 }
                        PathLine { x: card.width; y: 0 }
                        PathLine { x: card.width; y: card.height - root.chamfer }
                        PathLine { x: card.width - root.chamfer; y: card.height }
                        PathLine { x: 0; y: card.height }
                        PathLine { x: 0; y: 0 }
                    }
                }

                // Flare brackets on the three square corners.
                Row {
                    anchors.top: parent.top; anchors.left: parent.left
                    anchors.topMargin: -5; anchors.leftMargin: -5
                    Rectangle { width: 18; height: 3; color: root.phosphor }
                }
                Rectangle {
                    anchors.top: parent.top; anchors.left: parent.left
                    anchors.topMargin: -5; anchors.leftMargin: -5
                    width: 3; height: 18; color: root.phosphor
                }
                Row {
                    anchors.top: parent.top; anchors.right: parent.right
                    anchors.topMargin: -5; anchors.rightMargin: -5
                    Rectangle { width: 18; height: 3; color: root.phosphor }
                }
                Rectangle {
                    anchors.top: parent.top; anchors.right: parent.right
                    anchors.topMargin: -5; anchors.rightMargin: -5
                    width: 3; height: 18; color: root.phosphor
                }
                Row {
                    anchors.bottom: parent.bottom; anchors.left: parent.left
                    anchors.bottomMargin: -5; anchors.leftMargin: -5
                    Rectangle { width: 18; height: 3; color: root.phosphor }
                }
                Rectangle {
                    anchors.bottom: parent.bottom; anchors.left: parent.left
                    anchors.bottomMargin: -5; anchors.leftMargin: -5
                    width: 3; height: 18; color: root.phosphor
                }

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

                    Text {
                        visible: root.filter !== ""
                        text: "> " + root.filter.toUpperCase() + "  //  " + root.visibleEntries().length + " RITES"
                        color: root.bright
                        font.family: root.mono
                        font.pixelSize: 10
                        font.bold: true
                        font.letterSpacing: 1
                    }

                    Repeater {
                        model: root.visibleEntries()
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
                        text: "TYPE TO FILTER // RIGHT TO COMMIT // UP-DOWN TO SELECT // ESC TO WITHDRAW"
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
