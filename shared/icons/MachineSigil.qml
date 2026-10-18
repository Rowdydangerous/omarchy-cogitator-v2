import QtQuick
import QtQuick.Shapes

// Familiar symbols with shared industrial cuts and mounting details.
Item {
    id: icon
    property string kind: "slate"
    property color color: "white"
    property bool muted: false
    property bool enabledState: true
    property bool connected: false
    property bool inUse: false
    property bool multiple: false
    property real level: 1
    implicitWidth: 20; implicitHeight: 20
    readonly property string outline: {
        switch (kind) {
        case "bluetooth": return "M11 8L22 23L16 28V4L22 9L11 24M5 10L3 13V20L6 24M26 8L29 12V20L26 24"
        case "microphone": return "M12 3H20L23 6V16L20 20H12L9 16V6ZM5 14V20L10 25H22L27 20V14M16 25V30M10 30H22M12 9H20M12 13H20"
        case "monitor": return "M3 5H29V21L25 25H3ZM3 19H29M16 25V29M10 30H22M6 8H10M6 8V12M26 8H22"
        case "maintenance": return "M11 3L16 1L21 3L25 2L30 7L28 12L30 16L28 21L23 23M7 23L3 19L4 14L2 10L7 5ZM16 7V22M10 16L16 22L22 16M8 28H24"
        case "herald": return "M7 23V14L10 8L14 6V3H18V6L22 8L25 14V23L28 26H4ZM13 29H19M10 10H14"
        case "chrono": return "M9 3H23L29 9V23L23 29H9L3 23V9ZM16 6V9M6 16H9M23 16H26M16 23V26M16 10V16L22 20"
        default: return "M7 3H23L28 8V29H4V6ZM11 2H21V7H11ZM9 13H23M9 18H23M9 23H19"
        }
    }
    Item {
        width: 32; height: 32; anchors.centerIn: parent
        scale: Math.min(icon.width, icon.height) * 0.82 / 32
        opacity: icon.enabledState ? 1 : 0.45
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: icon.color; strokeWidth: 2; fillColor: "transparent"
                joinStyle: ShapePath.MiterJoin
                PathSvg { path: icon.outline }
            }
            ShapePath {
                strokeColor: icon.kind === "monitor" && icon.multiple ? icon.color : "transparent"
                strokeWidth: 1.5; fillColor: "transparent"
                PathSvg { path: "M8 2H31V18" }
            }
            ShapePath {
                strokeColor: icon.muted || !icon.enabledState ? icon.color : "transparent"
                strokeWidth: 2.5; fillColor: "transparent"
                PathMove { x: 2; y: 29 }
                PathLine { x: 29; y: 2 }
            }
        }
        Rectangle {
            visible: icon.kind === "microphone" && icon.inUse && !icon.muted
            x: 12; y: 6; width: 8; height: 3; color: icon.color
        }
        Rectangle {
            visible: icon.kind === "bluetooth" && icon.connected
            x: 26; y: 26; width: 4; height: 4; color: icon.color
        }
        Rectangle {
            visible: icon.kind === "monitor"
            x: 7; y: 22; width: 16 * Math.max(0, Math.min(1, icon.level)); height: 2
            color: icon.color
        }
    }
}
