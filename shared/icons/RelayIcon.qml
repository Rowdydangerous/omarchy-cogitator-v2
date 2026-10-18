import QtQuick
import QtQuick.Shapes
import "IconState.js" as IconState

Item {
    id: icon
    property color color: "white"
    property string kind: "disconnected"
    property int strength: -1
    readonly property int bands: IconState.signalBands(strength)
    implicitWidth: 20; implicitHeight: 20
    Item {
        width: 32; height: 32; anchors.centerIn: parent
        scale: Math.min(icon.width, icon.height) * 0.82 / 32
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: icon.color; strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: icon.kind === "ethernet"
                    ? "M6 4H26V18L22 22H10L6 18ZM16 22V29M9 29H23M10 4V10M14 4V10M18 4V10M22 4V10M10 14H22"
                    : "M16 17V28M11 29H21M13 24L16 20L19 24" }
            }
            ShapePath {
                strokeColor: icon.kind === "wifi" && icon.bands >= 1 ? icon.color : "transparent"
                strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: "M12 17Q16 13 20 17" }
            }
            ShapePath {
                strokeColor: icon.kind === "wifi" && icon.bands >= 2 ? icon.color : "transparent"
                strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: "M9 13Q16 6 23 13" }
            }
            ShapePath {
                strokeColor: icon.kind === "wifi" && icon.bands >= 3 ? icon.color : "transparent"
                strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: "M6 9Q16 -1 26 9" }
            }
            ShapePath {
                strokeColor: icon.kind === "wifi" && icon.bands >= 4 ? icon.color : "transparent"
                strokeWidth: 2; fillColor: "transparent"
                PathSvg { path: "M3 5Q16 -5 29 5" }
            }
            ShapePath {
                strokeColor: icon.kind === "disconnected" ? icon.color : "transparent"
                strokeWidth: 2.5; fillColor: "transparent"
                PathMove { x: 3; y: 27 }
                PathLine { x: 28; y: 3 }
            }
        }
        Rectangle { visible: icon.kind !== "ethernet"; x: 14; y: 16; width: 4; height: 4; color: icon.color }
    }
}
