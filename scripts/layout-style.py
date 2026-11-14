#!/usr/bin/env python3
"""Staged layout fixes; imported stock sources stay unchanged."""
from pathlib import Path


def agents_layout(file):
    file = Path(file)
    raw = file.read_text()
    start = raw.index("      id: dayLabel")
    end = raw.index("\n    }", start)
    label = raw[start:end]
    anchor = "      width: Style.space(52)"
    if anchor not in label:
        raise RuntimeError("Stock agent chart label changed; layout adapter needs review")
    label = label.replace(anchor, anchor + "\n      elide: Text.ElideRight", 1)
    file.write_text(raw[:start] + label + raw[end:])


def network_layout(file):
    file = Path(file)
    raw = file.read_text()
    anchor = "contentWidth: panel.fittedContentWidth(Style.space(380))"
    if anchor not in raw:
        raise RuntimeError("Stock network panel width changed; layout adapter needs review")
    raw = raw.replace(anchor, "contentWidth: panel.fittedContentWidth(Style.space(540))", 1)
    grid = "        GridLayout {\n          width: parent.width\n          columns: 4"
    if grid not in raw:
        raise RuntimeError("Stock network detail grid changed; layout adapter needs review")
    raw = raw.replace(grid, "        GridLayout {\n          width: parent.width\n          columns: width < Style.space(480) ? 2 : 4", 1)
    start = raw.index('          InfoLabel { text: "IP Address" }')
    end = raw.index("\n        }\n      }", start)
    addresses = raw[start:end]
    addresses = addresses.replace("          DetailValue {", "          DetailValue {\n            wrapMode: Text.WrapAnywhere\n            elide: Text.ElideNone")
    raw = raw[:start] + '''        }

        // Addresses each get their own row: never share a narrow four-column
        // metric row. Preserve full text for display, tooltips and copying.
        GridLayout {
          width: parent.width
          columns: 2
          columnSpacing: Style.space(20)
          rowSpacing: Style.spacing.labelGap
''' + addresses + raw[end:]
    # Both label/value pairs get deterministic column widths. Without these,
    # changing digit counts redistribute free space and move the right labels.
    start = raw.index("        GridLayout {", raw.index("// Connection details:"))
    end = raw.index("        // Addresses each get their own row:", start)
    metrics = raw[start:end]
    metrics = metrics.replace("          rowSpacing: Style.spacing.labelGap", '''          rowSpacing: Style.spacing.labelGap
          readonly property real pairWidth: Math.max(0, (width - columnSpacing * (columns - 1)) / (columns / 2))
          readonly property real labelWidth: Math.floor(pairWidth * (columns === 4 ? 0.55 : 0.45))
          readonly property real valueWidth: pairWidth - labelWidth''', 1)
    for component, dimension in (("InfoLabel", "labelWidth"), ("DetailValue", "valueWidth")):
        metrics = metrics.replace(component + " {", component + " {\n"
            + "            Layout.minimumWidth: parent." + dimension + "\n"
            + "            Layout.preferredWidth: parent." + dimension + "\n"
            + "            Layout.maximumWidth: parent." + dimension + "\n")
    raw = raw[:start] + metrics + raw[end:]
    raw = raw.replace("    Layout.fillWidth: true\n    horizontalAlignment: Text.AlignRight",
                      "    Layout.fillWidth: true\n    Layout.minimumWidth: 0\n    elide: Text.ElideRight\n    horizontalAlignment: Text.AlignRight", 1)
    raw = raw.replace("  component InfoLabel: Text {", "  component InfoLabel: Text {\n    Layout.minimumWidth: 0\n    Layout.maximumWidth: Math.max(1, parent.width * 0.45)\n    wrapMode: Text.Wrap", 1)
    file.write_text(raw)


def weather_layout(file):
    raw = Path(file).read_text()
    start = raw.index("      // ---- Hero row:")
    end = raw.index("      // ---- Geocoding suggestions", start)
    hero = raw[start:end]
    hero = hero.replace("      Item {", "      Column {", 1)
    hero = hero.replace("        height: Math.max(heroLeft.height, heroRight.height)", "        spacing: Style.space(16)", 1)
    hero = hero.replace('''          anchors.left: parent.left
          anchors.leftMargin: Style.space(16)
          anchors.verticalCenter: parent.verticalCenter''', '''          anchors.horizontalCenter: parent.horizontalCenter''', 1)
    icon_start = hero.index("          Text {\n            id: heroIcon")
    icon_end = hero.index("\n          Row {", icon_start)
    hero = hero[:icon_start] + '''          CogitatorIcons.WeatherIcon {
            id: heroIcon
            width: Style.space(56); height: width
            anchors.verticalCenter: parent.verticalCenter
            glyph: root.label
            color: root.bar ? root.bar.foreground : Color.foreground
          }
''' + hero[icon_end:]
    hero = hero.replace("font.pixelSize: 56", "font.pixelSize: 48", 1)
    hero = hero.replace('''          width: weatherStats.implicitWidth
          anchors.right: parent.right
          anchors.rightMargin: Style.space(20)
          anchors.verticalCenter: parent.verticalCenter''', '''          width: parent.width''', 1)
    hero = hero.replace('''          Row {
            visible: !root.editingLocation''', '''          Row {
            width: parent.width
            visible: !root.editingLocation''', 1)
    hero = hero.replace('''              text: (root.reportLocation || "").toUpperCase()''', '''              width: heroRight.width - Style.space(32)
              elide: Text.ElideRight
              text: (root.reportLocation || "").toUpperCase()''', 1)
    hero = hero.replace("width: Style.space(190)", "width: Math.max(80, heroRight.width - Style.space(30))", 1)
    hero = hero.replace('''            id: weatherStats
            visible:''', '''            id: weatherStats
            width: parent.width
            visible:''', 1)
    hero = hero.replace("spacing: Style.space(36)", "spacing: Style.space(12)", 1)
    hero = hero.replace('''            Column {
              spacing: Style.space(5)''', '''            Column {
              width: (weatherStats.width - weatherStats.spacing * 2) / 3
              spacing: Style.space(5)''')
    for label in ("FEELS", "WIND", "HUMID"):
        hero = hero.replace(f'''                text: "{label}"''', f'''                width: parent.width
                height: Style.font.bodySmall * 2.8
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
                text: "{label}"''', 1)
    # Preserve source bindings/actions; only layout and its local icon import differ.
    result = raw[:start] + hero + raw[end:]
    if 'import "icons" as CogitatorIcons' not in result:
        result = 'import "icons" as CogitatorIcons\n' + result
    Path(file).write_text(result)
