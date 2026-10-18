import QtQuick

// Fit legacy font symbols by their painted bounds, not their font's em box.
Item {
    id: icon
    property string text: ""
    property string fontFamily: "monospace"
    property color color: "white"
    implicitWidth: 20; implicitHeight: 20
    readonly property real fit: Math.min(width, height) * 0.82 / Math.max(1, metrics.tightBoundingRect.width, metrics.tightBoundingRect.height)
    TextMetrics { id: metrics; text: icon.text; font.family: icon.fontFamily; font.pixelSize: 32 }
    Text {
        id: glyph
        text: icon.text
        textFormat: Text.PlainText
        color: icon.color
        font.family: icon.fontFamily
        font.pixelSize: 32
        renderType: Text.NativeRendering
        x: icon.width / 2 - (metrics.tightBoundingRect.x + metrics.tightBoundingRect.width / 2) * icon.fit
        y: icon.height / 2 - (baselineOffset + metrics.tightBoundingRect.y + metrics.tightBoundingRect.height / 2) * icon.fit
        transform: Scale { origin.x: 0; origin.y: 0; xScale: icon.fit; yScale: icon.fit }
    }
}
