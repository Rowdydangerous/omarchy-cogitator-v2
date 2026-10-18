import QtQuick
import QtQuick.Shapes
import "IconState.js" as IconState

Item {
    id: icon
    property color color: "white"
    property real volume: 0
    property bool muted: false
    property bool available: true
    property bool headphones: false
    readonly property bool silenced: muted || !available || volume <= 0
    readonly property int bands: IconState.volumeBands(volume)
    implicitWidth: 20; implicitHeight: 20
    Item {
        width: 32; height: 32; anchors.centerIn: parent
        scale: Math.min(icon.width, icon.height) * 0.82 / 32
        opacity: icon.available ? 1 : 0.45
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: icon.color; strokeWidth: 1.8; fillColor: "transparent"
                PathSvg { path: icon.headphones
                    ? "M5 23V14C5 1 27 1 27 14V23M5 16H10V27H5ZM22 16H27V27H22Z"
                    : "M3 12H9L17 5V27L9 20H3ZM6 12V20M10 10V22" }
            }
            ShapePath {
                strokeColor: icon.color; strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: !icon.headphones && !icon.silenced && icon.bands >= 1 ? "M21 12Q25 16 21 20" : "" }
            }
            ShapePath {
                strokeColor: icon.color; strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: !icon.headphones && !icon.silenced && icon.bands >= 2 ? "M24 8Q32 16 24 24" : "" }
            }
            ShapePath {
                strokeColor: icon.color; strokeWidth: 1.5; fillColor: "transparent"
                PathSvg { path: !icon.headphones && !icon.silenced && icon.bands >= 3 ? "M27 4Q36 16 27 28" : "" }
            }
            ShapePath {
                strokeColor: icon.silenced ? icon.color : "transparent"; strokeWidth: 3
                fillColor: "transparent"
                PathMove { x: 3; y: 29 }
                PathLine { x: 28; y: 3 }
            }
        }
        Rectangle { x: 1; y: 10; width: 3; height: 3; color: icon.color }
        Rectangle { x: 1; y: 19; width: 3; height: 3; color: icon.color }
    }
}
