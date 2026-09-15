import QtQuick

// Subtle phosphor treatment for a bounded panel. Not a broken-TV filter:
// faint scanlines, soft edge falloff, whisper flicker, sparse animated grain.
// Everything pauses when not animated; grain costs one shared timer.
Item {
    id: root
    anchors.fill: parent

    property real intensity: 0.25
    property bool animated: true
    property real flicker: 0.05
    property real noise: 0.03
    property bool falloff: true

    property int grainTick: 0

    Timer {
        interval: 140
        running: root.animated && root.noise > 0 && root.visible
        repeat: true
        onTriggered: root.grainTick++
    }

    // Scanlines.
    Column {
        anchors.fill: parent
        spacing: 2
        Repeater {
            model: Math.max(0, Math.floor(parent.height / 3))
            Rectangle {
                width: parent.width
                height: 1
                color: Qt.rgba(0, 0, 0, 0.22 * root.intensity * 4 * 0.25 + 0.05)
            }
        }
    }

    // Edge falloff, top and bottom.
    Rectangle {
        visible: root.falloff
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 46
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(0, 0, 0, 0.35 * root.intensity * 4 * 0.25 + 0.08) }
            GradientStop { position: 1.0; color: "transparent" }
        }
    }
    Rectangle {
        visible: root.falloff
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 46
        gradient: Gradient {
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 1.0; color: Qt.rgba(0, 0, 0, 0.35 * root.intensity * 4 * 0.25 + 0.08) }
        }
    }

    // Sparse phosphor grain. Deterministic shimmer off one shared tick.
    Repeater {
        model: root.noise > 0 ? 18 : 0
        Rectangle {
            required property int index
            width: 2
            height: 2
            x: (index * 97 + 13) % Math.max(1, Math.floor(root.width - 2))
            y: (index * 61 + 7) % Math.max(1, Math.floor(root.height - 2))
            color: "#7dff9a"
            opacity: root.noise * (((index * 53 + root.grainTick * 29) % 17) / 16) * 0.5
        }
    }

    // Whisper flicker. Paused entirely unless animated.
    SequentialAnimation on opacity {
        running: root.animated && root.flicker > 0
        loops: Animation.Infinite
        NumberAnimation { to: 1.0 - root.flicker; duration: 140 }
        NumberAnimation { to: 1.0; duration: 220 }
        PauseAnimation { duration: 2600 }
    }
}
