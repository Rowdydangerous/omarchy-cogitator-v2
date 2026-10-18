#!/usr/bin/env python3
"""Weather layout adaptation: explicit stacked rows, bounded stat columns."""
from pathlib import Path


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
