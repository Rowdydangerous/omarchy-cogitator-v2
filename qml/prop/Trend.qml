import QtQuick

Item {
    id: root
    required property string title
    required property color ink
    required property color muted
    property var samples: []
    property bool fresh: true
    implicitHeight: 65

    onSamplesChanged: plot.requestPaint()
    onInkChanged: plot.requestPaint()
    onMutedChanged: plot.requestPaint()

    Text {
        text: root.title + (root.samples.length ? "  /  " + root.samples[root.samples.length - 1].value + "%" : "  /  --")
        color: root.ink
        font.family: "Monaspace Xenon Frozen, JetBrainsMono Nerd Font, monospace"
        font.pixelSize: 9
    }
    Text {
        anchors.right: parent.right
        text: !root.fresh ? "STALE" : (root.samples.length < 2 ? "COLLECTING" : "2 MIN / 0–100%")
        color: root.muted
        font.family: "Monaspace Xenon Frozen, JetBrainsMono Nerd Font, monospace"
        font.pixelSize: 8
    }
    Canvas {
        id: plot
        anchors { left: parent.left; right: parent.right; top: parent.top; bottom: parent.bottom; topMargin: 18 }
        opacity: root.fresh ? 1 : 0.45
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.strokeStyle = root.muted
            ctx.globalAlpha = 0.35
            ctx.lineWidth = 1
            for (var i = 0; i <= 2; i++) {
                var y = 1 + (height - 2) * i / 2
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke()
            }
            if (!root.samples.length) return
            var end = root.samples[root.samples.length - 1].time
            ctx.globalAlpha = 1
            ctx.strokeStyle = root.ink
            ctx.fillStyle = root.ink
            ctx.lineWidth = 1.5
            ctx.beginPath()
            for (var j = 0; j < root.samples.length; j++) {
                var point = root.samples[j]
                var x = Math.max(1, width - 2 - (end - point.time) / 120000 * (width - 4))
                var py = 1 + (height - 2) * (1 - point.value / 100)
                if (j === 0 || point.time - root.samples[j - 1].time > 15000) ctx.moveTo(x, py)
                else ctx.lineTo(x, py)
                if (root.samples.length === 1) ctx.fillRect(x - 1, py - 1, 2, 2)
            }
            ctx.stroke()
        }
    }
}
