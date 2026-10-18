import QtQuick
import QtQuick.Shapes

// Same 32-unit emblem as the original design, drawn directly in the scene.
// No image decoding, texture source, offscreen layer or tinting effect.
Item {
    id: icon
    property color color: "white"
    implicitWidth: 20
    implicitHeight: 20

    Item {
        width: 32
        height: 32
        anchors.centerIn: parent
        scale: Math.min(icon.width, icon.height) * 0.82 / 32

        Repeater {
            model: 8
            Rectangle {
                required property int index
                x: 14; y: 0
                width: 4; height: 6
                color: icon.color
                antialiasing: true
                transform: Rotation { origin.x: 2; origin.y: 16; angle: index * 45 }
            }
        }
        Rectangle {
            x: 3; y: 3
            width: 26; height: 26
            radius: 13
            color: "transparent"
            border.width: 3
            border.color: icon.color
            antialiasing: true
        }
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: "transparent"
                fillColor: icon.color
                fillRule: ShapePath.OddEvenFill
                PathSvg {
                    path: "M16 8c-4 0-7 2.5-7 6v4l3 2v4h8v-4l3-2v-4c0-3.5-3-6-7-6zm-5 6 4 1-1 3h-3zm6 1 4-1v4h-3zm-1 3-1.5 2h3zm-2.5 3h1v3h-1zm4 0h1v3h-1z"
                }
            }
        }
    }
}
