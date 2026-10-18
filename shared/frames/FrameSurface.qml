import QtQuick
import QtQuick.Shapes
import qs.Commons

// Rectangle-compatible geometry/insets; the fill itself has a cut corner.
Item {
    id: frame
    property color color: Color.popups.background
    property color outlineColor: Border.canUseNative(borderSpec) && Border.uniformWidth(borderSpec) > 0
                                 ? Border.color(borderSpec) : Color.accent
    property real cutSize: 30
    property bool drawOutline: true
    property bool drawFlares: true
    property real radius: 0 // Compatibility with stock card callers.
    property var borderSpec: Border.none()
    property real padding: 0
    property real topPadding: padding
    property real rightPadding: padding
    property real bottomPadding: padding
    property real leftPadding: padding
    readonly property real borderTop: Math.max(2, Border.top(borderSpec))
    readonly property real borderRight: Math.max(2, Border.right(borderSpec))
    readonly property real borderBottom: Math.max(2, Border.bottom(borderSpec))
    readonly property real borderLeft: Math.max(2, Border.left(borderSpec))
    readonly property real contentTopInset: borderTop + topPadding
    readonly property real contentRightInset: borderRight + rightPadding
    readonly property real contentBottomInset: borderBottom + bottomPadding
    readonly property real contentLeftInset: borderLeft + leftPadding
    readonly property real cut: drawOutline ? Math.min(cutSize, width / 4, height / 3) : cutSize

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: frame.drawOutline ? frame.outlineColor : "transparent"
            strokeWidth: frame.drawOutline ? 2 : 0
            fillColor: frame.color
            joinStyle: ShapePath.MiterJoin
            PathMove { x: 1; y: 1 }
            PathLine { x: frame.width - 1; y: 1 }
            PathLine { x: frame.width - 1; y: frame.height - frame.cut }
            PathLine { x: frame.width - frame.cut; y: frame.height - 1 }
            PathLine { x: 1; y: frame.height - 1 }
            PathLine { x: 1; y: 1 }
        }
    }
    // Three square-corner flares, matching the Command Nexus reference.
    Repeater {
        model: frame.drawFlares ? 3 : 0
        Item {
            required property int index
            x: index === 1 ? frame.width - 13 : -5
            y: index === 2 ? frame.height - 13 : -5
            width: 18; height: 18
            Rectangle { width: 18; height: 3; y: index === 2 ? 15 : 0; color: frame.outlineColor }
            Rectangle { width: 3; height: 18; x: index === 1 ? 15 : 0; color: frame.outlineColor }
        }
    }
}
