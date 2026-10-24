import QtQuick
import QtQuick.Controls as Controls
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui
import qs.Ui as Ui
import "frames" as Frames

Ui.Panel {
    id: root
    moduleName: "cogitator.control"
    ipcTarget: "cogitator.control"
    manageIpc: false
    readonly property string backend: decodeURIComponent(Qt.resolvedUrl("backend.py").toString().replace(/^file:\/\//, ""))
    property var reported: ({})
    property var saved: ({})
    property var draft: ({})
    property var fields: []
    property string revision: ""
    property string section: "Overview"
    property string message: ""
    property bool dirty: false
    readonly property bool engaged: reported.engaged === true
    readonly property bool busy: reported.busy === true || action.running
    readonly property bool failed: !!(reported.operation && reported.operation.phase === "failed")
    readonly property color ink: failed ? Color.yellow : Color.accent
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight

    function refresh() { if (!query.running) query.running = true }
    function choiceLabel(field, value) {
        return field.choiceLabels && field.choiceLabels[value] ? field.choiceLabels[value] : String(value)
    }
    function paletteLabel(value) {
        for (var i = 0; i < fields.length; i++)
            if (fields[i].key === "PALETTE") return choiceLabel(fields[i], value)
        return String(value)
    }
    function setValue(key, value) {
        var next = JSON.parse(JSON.stringify(draft))
        next[key] = value
        draft = next
        dirty = JSON.stringify(draft) !== JSON.stringify(saved)
    }
    function revert() { dirty = false; message = ""; refresh() }
    function invoke(operation) {
        if (busy) return
        if (operation !== "save" && dirty) {
            message = "Apply or Revert your edits before switching mode."
            return
        }
        var command = ["python3", backend, operation]
        if (operation === "save") {
            var changed = []
            for (var key in draft) if (draft[key] !== saved[key]) changed.push(key)
            command.push(JSON.stringify({values: draft, revision: revision, changed: changed}))
        }
        action.command = command
        action.running = true
    }
    function visibleFields() {
        return fields.filter(function(field) { return field.group === root.section })
    }
    function channel(hex, index) {
        var value = String(hex || "#4fd06a").replace("#", "")
        if (value.length === 3) value = value.split("").map(function(c) { return c + c }).join("")
        return /^[0-9a-fA-F]{6}$/.test(value) ? parseInt(value.substring(index * 2, index * 2 + 2), 16) : 0
    }
    function setChannel(index, value) {
        var channels = [channel(draft.CUSTOM_PHOSPHOR, 0), channel(draft.CUSTOM_PHOSPHOR, 1), channel(draft.CUSTOM_PHOSPHOR, 2)]
        channels[index] = Math.round(value)
        setValue("CUSTOM_PHOSPHOR", "#" + channels.map(function(c) { return ("0" + c.toString(16)).slice(-2) }).join(""))
    }

    onOpenedChanged: if (opened) refresh()
    Component.onCompleted: refresh()
    IpcHandler {
        target: "cogitator.control"
        function open(): void { root.open() }
        function close(): void { root.close() }
        function toggle(): void { root.toggle() }
        function page(name: string): void {
            if (["Overview", "Appearance", "Surfaces", "Motion"].indexOf(name) !== -1) root.section = name
            root.open()
        }
    }
    Timer { interval: root.opened ? 2000 : 10000; running: true; repeat: true; onTriggered: root.refresh() }
    Process {
        id: query
        command: ["python3", root.backend, "status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var data = JSON.parse(text)
                    if (!data.values) { root.message = data.message || "Status unavailable"; return }
                    root.reported = data
                    root.fields = data.schema
                    if (!root.dirty) {
                        root.saved = data.values
                        root.draft = JSON.parse(JSON.stringify(data.values))
                        root.revision = data.revision
                    }
                } catch (error) { root.message = "Status could not be read: " + error }
            }
        }
    }
    Process {
        id: action
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    root.message = result.message || "Directive submitted"
                    if (result.ok) root.dirty = false
                } catch (error) { root.message = "Directive failed; inspect transition logs." }
            }
        }
        onExited: root.refresh()
    }

    BarIconButton {
        id: button
        bar: root.bar
        text: ""
        iconComponent: Component {
            CogSkull { color: root.ink }
        }
        opacity: root.engaged || root.busy || root.failed ? 1 : 0.55
        onPressed: function(mouseButton) { if (mouseButton === Qt.LeftButton) root.toggle() }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            width: root.engaged ? 12 : 7; height: 2
            color: root.ink
            opacity: root.busy ? 0.3 : 1
            SequentialAnimation on opacity {
                running: root.busy; loops: Animation.Infinite
                NumberAnimation { to: 0.2; duration: 500 }
                NumberAnimation { to: 1; duration: 500 }
            }
        }
    }

    Frames.KeyboardPanel {
        id: popup
        anchorItem: button
        owner: root
        bar: root.bar
        open: root.opened
        contentWidth: fittedContentWidth(560)
        contentHeight: cappedContentHeight(root.section === "Overview" ? 420 : 650)
        focusTarget: keyCatcher

        Item {
            id: keyCatcher
            anchors.fill: parent
            focus: true
            Keys.onEscapePressed: root.close()
            Column {
                id: header
                anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                spacing: 10
                Text { text: "COGITATOR CONTROL SANCTUM"; color: Color.accent; font.family: Style.font.family; font.pixelSize: 18; font.bold: true }
                Text {
                    text: root.busy ? "+++ TRANSITION IN PROGRESS +++" : (root.engaged ? "MACHINE SPIRIT ENGAGED" : "MACHINE SPIRIT DISENGAGED")
                    color: root.ink; font.family: Style.font.family; font.pixelSize: 12
                }
                Row {
                    spacing: 4
                    Repeater {
                        model: ["Overview", "Appearance", "Surfaces", "Motion"]
                        Controls.Button {
                            required property string modelData
                            text: modelData
                            highlighted: root.section === modelData
                            onClicked: root.section = modelData
                        }
                    }
                }
                Rectangle { width: parent.width; height: 1; color: Color.accent; opacity: 0.5 }
            }
            Controls.ScrollView {
                anchors.left: parent.left; anchors.right: parent.right
                anchors.top: header.bottom; anchors.topMargin: 12
                anchors.bottom: footer.top; anchors.bottomMargin: 10
                clip: true
                contentWidth: availableWidth
                Column {
                    id: body
                    width: popup.contentWidth - popup.padding * 2 - 4
                    spacing: 14
                    Column {
                        width: parent.width; spacing: 14
                        visible: root.section === "Overview"
                        Text { text: "MODE DIRECTIVE"; color: Color.accent; font.family: Style.font.family; font.pixelSize: 13 }
                        Controls.Button {
                            text: root.busy ? "Performing rite…" : (root.engaged ? "Disengage Cogitator" : "Engage Cogitator")
                            enabled: !root.busy && !root.dirty
                            onClicked: root.invoke(root.engaged ? "disengage" : "engage")
                        }
                        Controls.Button {
                            text: "Update from GitHub"
                            enabled: !root.busy && !root.dirty
                            onClicked: root.invoke("update")
                        }
                        Text {
                            width: parent.width; wrapMode: Text.WordWrap
                            text: "Theme changes restart terminals. The control widget remains available when Cogitator is disengaged."
                            color: Color.foreground; font.family: Style.font.family; font.pixelSize: 13
                        }
                        Text {
                            width: parent.width; wrapMode: Text.WordWrap
                            text: "Phosphor doctrine: " + root.paletteLabel(root.saved.PALETTE || "green").toUpperCase() + "\nSuite: " + String(root.reported.suite || "inactive")
                            color: Color.foreground; font.family: Style.font.family; font.pixelSize: 13
                        }
                        Text {
                            width: parent.width; wrapMode: Text.WordWrap
                            text: root.reported.operation ? root.reported.operation.message || "" : ""
                            color: root.failed ? Color.yellow : Color.foreground
                            font.family: Style.font.family; font.pixelSize: 13
                        }
                        Controls.Button {
                            visible: root.failed; enabled: !root.busy
                            text: "Review transition logs"
                            onClicked: {
                                action.command = ["python3", root.backend, "logs"]
                                action.running = true
                            }
                        }
                    }
                    Repeater {
                        model: root.visibleFields()
                        SettingRow { required property var modelData; field: modelData; width: body.width }
                    }
                }
            }
            Column {
                id: footer
                anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
                spacing: 8
                Text {
                    width: parent.width; wrapMode: Text.WordWrap
                    text: root.message || (root.dirty ? "UNSAVED DIRECTIVES" : (root.engaged ? "Configuration synchronized" : "Settings apply on next engagement"))
                    color: root.dirty || root.failed ? Color.yellow : Color.foreground
                    font.family: Style.font.family; font.pixelSize: 12
                }
                Row {
                    spacing: 8
                    Controls.Button { text: "Apply"; enabled: root.dirty && !root.busy; onClicked: root.invoke("save") }
                    Controls.Button { text: "Revert"; enabled: root.dirty && !root.busy; onClicked: root.revert() }
                    Controls.Button { text: "Close"; onClicked: root.close() }
                }
            }
        }
    }

    component SettingRow: Column {
        id: row
        required property var field
        property bool colorExpanded: false
        spacing: 5
        Text { text: row.field.label; color: Color.foreground; font.family: Style.font.family; font.pixelSize: 13 }
        Controls.CheckBox {
            visible: row.field.type === "boolean"
            text: checked ? "Enabled" : "Disabled"
            checked: root.draft[row.field.key] === true
            enabled: !root.busy
            onToggled: root.setValue(row.field.key, checked)
        }
        Controls.ComboBox {
            visible: row.field.type === "choice"
            width: 220
            model: (row.field.choices || []).map(function(value) {
                return {value: value, label: root.choiceLabel(row.field, value)}
            })
            textRole: "label"
            valueRole: "value"
            currentIndex: (row.field.choices || []).indexOf(String(root.draft[row.field.key]))
            enabled: !root.busy
            onActivated: function(index) { root.setValue(row.field.key, model[index].value) }
        }
        Row {
            visible: row.field.key === "PALETTE"
            spacing: 10
            Repeater {
                model: ["#4fd06a", "#e0ad2f", "#ff5345", "#b4ad91"]
                Rectangle {
                    required property int index
                    required property string modelData
                    width: 28; height: 20; color: modelData
                    border.width: root.draft.PALETTE === ["green", "amber", "red", "industrial"][index] ? 3 : 1
                    border.color: Color.foreground
                    Controls.ToolTip.visible: swatchMouse.containsMouse
                    Controls.ToolTip.text: root.paletteLabel(["green", "amber", "red", "industrial"][index])
                    MouseArea {
                        id: swatchMouse
                        hoverEnabled: true
                        anchors.fill: parent; cursorShape: Qt.PointingHandCursor; enabled: !root.busy
                        onClicked: root.setValue("PALETTE", ["green", "amber", "red", "industrial"][parent.index])
                    }
                }
            }
        }
        Row {
            visible: row.field.type === "number"
            width: parent.width; spacing: 12
            PanelSlider {
                bar: root.bar; width: parent.width - 65
                minimum: row.field.min || 0; maximum: row.field.max || 1; step: row.field.step || 0.01
                integer: row.field.step === 1
                value: Number(root.draft[row.field.key] || 0)
                enabled: !root.busy
                onReleased: function(value) { root.setValue(row.field.key, Number(value.toFixed(2))) }
            }
            Text { text: Number(root.draft[row.field.key] || 0).toFixed(row.field.step === 1 ? 0 : 2); color: Color.accent; font.family: Style.font.family; font.pixelSize: 13 }
        }
        Row {
            visible: row.field.type === "color"
            spacing: 12
            Controls.TextField {
                width: 180; placeholderText: "#7CFF6B"
                text: String(root.draft[row.field.key] || "")
                enabled: !root.busy
                onTextEdited: root.setValue(row.field.key, text)
            }
            Rectangle {
                width: 34; height: 34
                color: /^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$/.test(String(root.draft[row.field.key])) ? root.draft[row.field.key] : "#4fd06a"
                border.color: Color.foreground
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: row.colorExpanded = !row.colorExpanded }
            }
            Controls.Button { text: "RGB picker"; onClicked: row.colorExpanded = !row.colorExpanded }
        }
        Column {
            visible: row.field.type === "color" && row.colorExpanded
            width: parent.width; spacing: 5
            Repeater {
                model: ["Red", "Green", "Blue"]
                Row {
                    required property int index
                    required property string modelData
                    width: row.width; spacing: 8
                    Text { width: 50; text: modelData; color: Color.foreground; font.family: Style.font.family; font.pixelSize: 12 }
                    PanelSlider {
                        bar: root.bar; width: row.width - 80
                        minimum: 0; maximum: 255; integer: true; step: 1
                        value: root.channel(root.draft.CUSTOM_PHOSPHOR, parent.index)
                        enabled: !root.busy
                        onReleased: function(value) { root.setChannel(parent.index, value) }
                    }
                }
            }
        }
    }
}
