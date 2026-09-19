// Cogitator notification card (rowdy.notifications clone).
// Presentational only — same props/signals contract as stock, so the
// daemon, history panel, timeouts, DND, and actions are untouched.
// Visual language follows the Secret-Level directives: corner-bracket
// framing, one chamfered (cut) corner, a header tab straddling the top
// edge, and a glowing phosphor fill with dark text for critical alerts.

import QtQuick
import QtQuick.Layouts
import QtQuick.Shapes
import Quickshell
import qs.Commons
import qs.Ui
import "../NotificationLogic.js" as NotificationLogic

BorderSurface {
  id: root

  property string app: ""
  property string appIcon: ""
  property string summary: ""
  property string body: ""
  property string image: ""
  // Nerd Font glyph rendered in the icon slot when no real icon is set.
  property string glyph: ""
  // NotificationUrgency: Low=0, Normal=1, Critical=2 (upstream).
  property int urgency: 1
  property double timestamp: 0
  property int cornerRadius: 0

  // System monospace font injected by the container.
  property string fontFamily: ""

  readonly property bool hovered: hoverTracker.hovered

  signal closeRequested()
  signal cardClicked()

  readonly property string smallIconSource: image.length > 0 ? image : iconSource(appIcon)
  readonly property bool hasGlyph: glyph.length > 0
  readonly property bool compactGlyph: NotificationLogic.shouldRenderCompactGlyph(glyph, smallIconSource, singleLineToast)
  readonly property bool hasSmallIcon: smallIconSource.length > 0
  readonly property bool summaryStartsWithGlyph: NotificationLogic.summaryStartsWithGlyph(summary)
  readonly property bool singleLineToast: sanitizedBody.length === 0
  readonly property bool collapseRedundantIcon: singleLineToast && !hasGlyph && summaryStartsWithGlyph
  readonly property string sanitizedBody: sanitizeBody(body)
  readonly property string styledBody: NotificationLogic.styledBody(body, app, appIcon)

  readonly property bool critical: urgency === 2
  readonly property string riteWord: critical ? "CRITICAL" : (urgency === 0 ? "NOTICE" : "ADVISORY")
  readonly property string mono: "Monaspace Xenon Frozen, JetBrainsMono Nerd Font, monospace"
  readonly property color ink: critical ? Qt.darker(Color.notifications.countdown, 3.2) : Color.notifications.text
  readonly property color faintInk: critical ? Qt.darker(Color.notifications.countdown, 2.2) : Qt.darker(Color.notifications.text, 1.4)
  readonly property color frameColor: critical ? Color.notifications.countdown : Color.notifications.border
  readonly property real chamfer: 30

  function sanitizeBody(s) {
    return NotificationLogic.sanitizeBody(s, app, appIcon)
  }

  function iconSource(icon) {
    var value = String(icon || "")
    if (value.length === 0) return ""
    if (value.indexOf("file://") === 0 || value.indexOf("image://") === 0) return value
    if (value.charAt(0) === "/") return Util.fileUrl(value)
    return Quickshell.iconPath(value, true)
  }

  implicitWidth: Style.space(520)
  implicitHeight: mainColumn.implicitHeight + headerTab.height / 2 + Style.space(14)
  radius: 0
  color: critical ? Color.notifications.countdown : Qt.rgba(Color.notifications.background.r, Color.notifications.background.g, Color.notifications.background.b, 0.96)
  borderSpec: Border.none()
  clip: false

  HoverHandler { id: hoverTracker }

  MouseArea {
    anchors.fill: parent
    cursorShape: Qt.PointingHandCursor
    acceptedButtons: Qt.LeftButton | Qt.RightButton
    onClicked: function(mouse) {
      if (mouse.button === Qt.RightButton) {
        root.closeRequested()
      } else {
        root.cardClicked()
      }
    }
  }

  // Chamfered frame: full outline with the bottom-right corner cut at 45°.
  Shape {
    anchors.fill: parent
    preferredRendererType: Shape.CurveRenderer
    ShapePath {
      strokeColor: root.frameColor
      strokeWidth: 2
      fillColor: "transparent"
      PathMove { x: 0; y: 0 }
      PathLine { x: root.width; y: 0 }
      PathLine { x: root.width; y: root.height - root.chamfer }
      PathLine { x: root.width - root.chamfer; y: root.height }
      PathLine { x: 0; y: root.height }
      PathLine { x: 0; y: 0 }
    }
  }

  // Corner brackets on the three square corners.
  Row {
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.topMargin: -5
    anchors.leftMargin: -5
    spacing: 0
    Rectangle { width: 18; height: 3; color: root.frameColor }
  }
  Rectangle {
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.topMargin: -5
    anchors.leftMargin: -5
    width: 3
    height: 18
    color: root.frameColor
  }
  Row {
    anchors.top: parent.top
    anchors.right: parent.right
    anchors.topMargin: -5
    anchors.rightMargin: -5
    Rectangle { width: 18; height: 3; color: root.frameColor }
  }
  Rectangle {
    anchors.top: parent.top
    anchors.right: parent.right
    anchors.topMargin: -5
    anchors.rightMargin: -5
    width: 3
    height: 18
    color: root.frameColor
  }
  Row {
    anchors.bottom: parent.bottom
    anchors.left: parent.left
    anchors.bottomMargin: -5
    anchors.leftMargin: -5
    Rectangle { width: 18; height: 3; color: root.frameColor }
  }
  Rectangle {
    anchors.bottom: parent.bottom
    anchors.left: parent.left
    anchors.bottomMargin: -5
    anchors.leftMargin: -5
    width: 3
    height: 18
    color: root.frameColor
  }

  // Header tab straddling the top edge: severity + origin.
  Rectangle {
    id: headerTab
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.top: parent.top
    anchors.topMargin: -13
    width: Math.min(tabText.implicitWidth + 36, parent.width - 60)
    height: 26
    color: critical ? Color.notifications.countdown : Color.notifications.background
    border.color: root.frameColor
    border.width: 1
    Text {
      id: tabText
      anchors.centerIn: parent
      textFormat: Text.PlainText
      text: root.riteWord + (root.app.length > 0 ? " // " + root.app.toUpperCase() : "")
      color: root.ink
      font.family: root.mono
      font.pixelSize: Style.font.caption
      font.bold: true
      font.letterSpacing: 2
      elide: Text.ElideRight
    }
  }

  ColumnLayout {
    id: mainColumn
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.top: parent.top
    anchors.topMargin: headerTab.height / 2 + Style.space(8)
    anchors.leftMargin: Style.space(16)
    anchors.rightMargin: Style.space(16)
    anchors.bottomMargin: Style.space(10)
    spacing: 0

    RowLayout {
      Layout.fillWidth: true
      spacing: root.collapseRedundantIcon ? 0 : Style.space(12)

      Item {
        id: smallIconSlot
        Layout.preferredWidth: visible ? Style.space(40) : 0
        Layout.preferredHeight: visible ? Style.space(40) : 0
        Layout.alignment: Qt.AlignVCenter
        visible: !root.collapseRedundantIcon && !root.compactGlyph && (root.hasSmallIcon || root.hasGlyph) && (root.hasGlyph || smallIconImage.status !== Image.Error)

        Image {
          id: smallIconImage
          anchors.fill: parent
          source: root.smallIconSource
          sourceSize.width: smallIconSlot.width * Screen.devicePixelRatio
          sourceSize.height: smallIconSlot.height * Screen.devicePixelRatio
          fillMode: Image.PreserveAspectFit
          asynchronous: true
          smooth: true
          visible: !root.hasGlyph || smallIconImage.status === Image.Ready
        }

        Text {
          textFormat: Text.PlainText
          anchors.centerIn: parent
          visible: root.hasGlyph && smallIconImage.status !== Image.Ready
          text: root.glyph
          color: root.ink
          font.family: root.fontFamily
          font.pixelSize: Style.font.displayLarge
        }
      }

      ColumnLayout {
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignVCenter
        spacing: Style.space(4)

        Text {
          textFormat: Text.PlainText
          Layout.fillWidth: true
          visible: root.summary.length > 0
          text: root.summary.toUpperCase()
          font.family: root.mono
          color: root.ink
          font.pixelSize: root.critical ? Style.font.display : Style.font.title
          font.bold: true
          font.letterSpacing: root.critical ? 3 : 1
          wrapMode: Text.WordWrap
          elide: Text.ElideRight
          maximumLineCount: 2
          horizontalAlignment: root.critical && root.singleLineToast ? Text.AlignHCenter : Text.AlignLeft
        }

        Text {
          Layout.fillWidth: true
          Layout.topMargin: Style.space(2)
          visible: root.sanitizedBody.length > 0
          text: root.styledBody
          textFormat: Text.StyledText
          font.family: root.mono
          color: root.faintInk
          font.pixelSize: Style.font.body
          wrapMode: Text.WordWrap
          elide: Text.ElideRight
          maximumLineCount: 3
        }
      }
    }
  }
}
