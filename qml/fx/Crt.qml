import QtQuick

// Subtle phosphor treatment for a bounded panel. Not a broken-TV filter:
// faint scanlines, soft edge falloff, optional whisper flicker.
Item {
    id: root
    anchors.fill: parent

    property real intensity: 0.25
    property bool animated: true
    property real flicker: 0.05

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
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 46
        gradient: Gradient {
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 1.0; color: Qt.rgba(0, 0, 0, 0.35 * root.intensity * 4 * 0.25 + 0.08) }
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
