import QtQuick
import QtQuick.Shapes
import "IconState.js" as IconState

Item {
    id: icon
    property color color: "white"
    property color backdrop: "black"
    property real fraction: 0
    property bool charging: false
    property bool present: true
    readonly property real charge: IconState.cellCharge(fraction)
    implicitWidth: 20; implicitHeight: 20
    Item {
        width: 32; height: 32; anchors.centerIn: parent
        scale: Math.min(icon.width, icon.height) * 0.82 / 32
        Rectangle { visible: icon.present; x: 13; y: 1; width: 6; height: 4; color: icon.color }
        Rectangle { visible: icon.present; x: 11; y: 26 - 16 * icon.charge; width: 10; height: 16 * icon.charge; color: icon.color }
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: icon.color; strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: icon.present
                    ? "M8 6H24V25L20 29H8ZM5 11H8M5 23H8M24 11H27M24 23H27"
                    : "M10 3V11M22 3V11M7 11H25V18L21 22H11L7 18ZM16 22V29M11 29H21" }
            }
            ShapePath {
                strokeColor: icon.charging && icon.present ? icon.backdrop : "transparent"
                strokeWidth: 3; fillColor: icon.charging && icon.present ? icon.color : "transparent"
                PathSvg { path: "M18 8L11 18H16L14 25L22 14H17Z" }
            }
        }
    }
}
