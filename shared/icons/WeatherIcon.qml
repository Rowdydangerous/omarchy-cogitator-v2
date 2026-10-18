import QtQuick
import QtQuick.Shapes
import "IconState.js" as IconState

Item {
    id: icon
    property color color: "white"
    property string glyph: ""
    readonly property string condition: IconState.weatherKind(glyph)
    readonly property bool cloud: ["cloud", "partly", "partly-night", "rain", "snow", "sleet", "storm", "fog"].indexOf(condition) !== -1
    implicitWidth: 20; implicitHeight: 20
    Item {
        width: 32; height: 32; anchors.centerIn: parent
        scale: Math.min(icon.width, icon.height) * 0.82 / 32
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: icon.color; strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: icon.cloud ? "M3 21V16L7 13H11L14 8H21L25 12V15H28L30 18V23H3Z" : "" }
            }
            ShapePath {
                strokeColor: icon.color; strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: icon.condition === "sun" ? "M11 7H21L25 11V21L21 25H11L7 21V11ZM16 0V4M16 28V32M0 16H4M28 16H32M3 3L6 6M26 26L29 29M3 29L6 26M26 6L29 3" :
                    (icon.condition === "moon" ? "M21 3C3 0 0 24 16 28C23 30 29 25 30 20C18 24 13 12 21 3Z" :
                    (icon.condition === "partly" ? "M5 10V5H10M2 3L5 6M11 1V5M1 11H5" :
                    (icon.condition === "partly-night" ? "M11 2C1 1 0 11 7 14M11 2C7 6 9 9 12 10" : ""))) }
            }
            ShapePath {
                strokeColor: icon.color; strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: icon.condition === "rain" ? "M8 26L5 31M17 26L14 31M26 26L23 31" :
                    (icon.condition === "snow" ? "M9 25V32M5 27L13 31M5 31L13 27M24 25V32M20 27L28 31M20 31L28 27" :
                    (icon.condition === "sleet" ? "M7 26L4 31M17 27V31M15 29H19M25 26L22 31" :
                    (icon.condition === "storm" ? "M17 20L11 27H16L14 32L23 24H18Z" :
                    (icon.condition === "fog" ? "M3 27H29M7 31H25" : "")))) }
            }
            ShapePath {
                strokeColor: icon.condition === "unknown" ? icon.color : "transparent"
                strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: "M16 2L30 16L16 30L2 16ZM12 11Q16 5 21 11Q24 16 16 19V22M16 25V27" }
            }
        }
    }
}
