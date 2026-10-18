#!/usr/bin/env python3
"""Package native industrial icons; preserve stock device/action models."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def replace_once(raw, old, new):
    if raw.count(old) != 1:
        raise RuntimeError("Icon overlay anchor drift: " + old[:80])
    return raw.replace(old, new, 1)


def apply_icons(stage, root=ROOT):
    if not (root / "shared/icons").exists():
        return False
    manifest = json.loads((stage / "manifest.json").read_text())
    domain = manifest["id"].removeprefix("cogitator.")
    files = {"audio": "Panel.qml", "network": "Panel.qml", "power": "Panel.qml",
             "bluetooth": "Panel.qml", "monitor": "Panel.qml", "microphone": "Microphone.qml",
             "weather": "BarWidget.qml", "system-update": "SystemUpdate.qml",
             "indicators": "indicators/Dnd.qml", "clipboard": "Clipboard.qml", "clock": "Panel.qml",
             "agents": "Panel.qml"}
    if domain not in files:
        return False
    file = stage / files[domain]
    raw = file.read_text()
    if domain == "audio":
        raw = replace_once(raw, '    text: root.outputIcon()\n    onPressed:', '''    text: ""
    iconComponent: Component {
      CogitatorIcons.VoxIcon {
        color: button.foreground
        volume: root.outputVolume
        muted: root.outputMuted
        available: root.hasOutput
        headphones: root.isHeadphones(root.sink)
      }
    }
    tooltipText: "Vox Array — Audio\\n" + (!root.hasOutput ? "No output device" :
      (root.outputMuted ? "Muted" : Math.round(root.outputVolume * 100) + "% volume"))
    onPressed:''')
    elif domain == "network":
        raw = replace_once(raw, '    bar: root.bar\n    text: root.icon\n\n    onPressed:', '''    bar: root.bar
    text: ""
    iconComponent: Component {
      CogitatorIcons.RelayIcon {
        color: button.foreground
        kind: root.kind
        strength: root.signalStrength
      }
    }
    tooltipText: "Noospheric Relay — Network\\n" + (root.kind === "ethernet" ? "Hardline connected" :
      (root.kind === "wifi" ? "Wireless link · " + root.signalStrength + "% signal" : "Disconnected"))
    onPressed:''')
    elif domain == "power":
        raw = replace_once(raw, 'showPercentage && !button.vertical ? button.glyphPaintedWidth : 0',
                           'root.showPercentage && !button.vertical ? button.width : 0')
        raw = replace_once(raw, '    slotSize: Style.bar.iconSlot * (root.showPercentage && !vertical ? 2 : 1)\n    tooltipText: ""', '''    TextMetrics {
      id: reserveMetrics
      text: Math.round(root.batteryFraction * 100) + "%"
      font.family: button.fontFamily
      font.pixelSize: button.fontSize
    }
    slotSize: root.showPercentage && !vertical ? Style.bar.iconSlot + reserveMetrics.width + Style.space(4) : Style.bar.iconSlot
    iconComponent: Component {
      Item {
        Row {
          anchors.centerIn: parent
          spacing: Style.space(4)
          Text {
            visible: root.showPercentage && !button.vertical
            text: Math.round(root.batteryFraction * 100) + "%"
            color: button.foreground
            font.family: button.fontFamily
            font.pixelSize: button.fontSize
            anchors.verticalCenter: parent.verticalCenter
          }
          CogitatorIcons.PowerCellIcon {
            width: button.opticalSize; height: button.opticalSize
            color: root.discharging && root.batteryFraction <= 0.10 ? Color.urgent : button.foreground
            backdrop: root.bar ? root.bar.background : Color.background
            fraction: root.batteryFraction
            charging: root.charging
            present: root.batteryPresent
          }
        }
      }
    }
    tooltipText: "Power Reserve — Battery\\n" + (!root.batteryPresent ? "External supply" :
      Math.round(root.batteryFraction * 100) + "% · " + (root.charging ? "Charging" : (root.discharging ? "Discharging" : "External power")))''')
    elif domain == "bluetooth":
        raw = replace_once(raw, '    bar: root.bar\n    text: root.icon\n    onPressed:', '''    bar: root.bar
    text: ""
    iconComponent: Component {
      CogitatorIcons.MachineSigil {
        kind: "bluetooth"; color: button.foreground
        enabledState: !!(root.adapter && root.adapter.enabled)
        connected: root.connectedDevices.length > 0
      }
    }
    tooltipText: "Auxiliary Links — Bluetooth\\n" + (!root.adapter ? "No adapter" : (!root.adapter.enabled ? "Disabled" : root.connectedDevices.length + " connected"))
    onPressed:''')
    elif domain == "monitor":
        raw = replace_once(raw, '    text: Quickshell.screens.length > 1 ? "󰍺" : "󰍹"', '''    text: ""
    iconComponent: Component {
      CogitatorIcons.MachineSigil {
        kind: "monitor"; color: button.foreground
        multiple: Quickshell.screens.length > 1
        level: root.brightnessPercent / 100
      }
    }
    tooltipText: "Optic Array — Display\\n" + (root.brightnessAvailable ? Math.round(root.brightnessPercent) + "% brightness" : "Display controls")''')
    elif domain == "microphone":
        raw = replace_once(raw, '    text: root.muted ? "󰍭" : "󰍬"', '''    text: ""
    iconComponent: Component {
      CogitatorIcons.MachineSigil {
        kind: "microphone"
        color: root.inUse ? button.activeColor : button.foreground
        muted: root.muted; inUse: root.inUse
      }
    }''')
        # The voice overlay may already have translated the stock tooltip.
        lines = raw.splitlines()
        lines = ['    tooltipText: "Vox Acquisition — Microphone\\n" + (root.muted ? "Muted" : (root.inUse ? "In use" : "Ready"))'
                 if line.strip().startswith("tooltipText:") else line for line in lines]
        raw = "\n".join(lines) + "\n"
    elif domain == "system-update":
        raw = replace_once(raw, '    text: "\\uf021"', '''    text: ""
    iconComponent: Component {
      CogitatorIcons.MachineSigil { kind: "maintenance"; color: button.foreground }
    }''')
    elif domain == "weather":
        raw = replace_once(raw, '    text: panelLoader.item ? panelLoader.item.label : ""', '''    text: ""
    iconComponent: Component {
      CogitatorIcons.WeatherIcon { color: button.foreground; glyph: panelLoader.item ? panelLoader.item.label : "" }
    }''')
        raw = replace_once(raw, '    tooltipText: ""', '''    tooltipText: "Atmospheric Auspex — Weather" + (panelLoader.item && panelLoader.item.reportTempNum !== ""
      ? "\\n" + panelLoader.item.reportTempNum + (panelLoader.item.useImperial ? "°F" : "°C") : "")''')
    elif domain == "indicators":
        raw = replace_once(raw, '  active: dnd', '''  iconComponent: Component {
    CogitatorIcons.MachineSigil { kind: "herald"; color: root.foreground; muted: root.dnd }
  }
  active: dnd''')
        raw = replace_once(raw, '  activeTooltipText: "Allow Notifications"', '  activeTooltipText: "Machine Herald — Notifications\\nSilenced · click to allow"')
        raw = replace_once(raw, '  inactiveTooltipText: "Silence Notifications"', '  inactiveTooltipText: "Machine Herald — Notifications\\nAllowed · click to silence"')
    elif domain == "clipboard":
        raw = replace_once(raw, '''          Text {
            textFormat: Text.PlainText
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            text: root.filterText''', '''          CogitatorIcons.MachineSigil {
            kind: "slate"; color: root.foreground
            width: Style.space(28); height: width
            anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
          }
          Text {
            textFormat: Text.PlainText
            anchors.left: parent.left
            anchors.leftMargin: Style.space(38)
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            text: root.filterText''')
    elif domain == "clock":
        start = raw.find('              Text {\n                // Baseline-aligned')
        end = raw.find('\n              Text {\n                id: heroDate', start)
        if start < 0 or end < 0:
            raise RuntimeError("Clock identity icon anchor drift")
        raw = raw[:start] + '''              CogitatorIcons.MachineSigil {
                kind: "chrono"
                width: 48; height: 48
                anchors.verticalCenter: heroDate.verticalCenter
                color: heroMouse.containsMouse ? Color.accent : root.contentForeground
              }
''' + raw[end:]
    elif domain == "agents":
        raw = replace_once(raw, '    text: "󱚣"', '''    text: "󱚣"
    iconComponent: Component {
      CogitatorIcons.GlyphIcon {
        text: button.text; fontFamily: button.fontFamily
        color: button.active ? button.activeColor : button.foreground
      }
    }''')
    relative = "../icons" if domain == "indicators" else "icons"
    file.write_text(f'import "{relative}" as CogitatorIcons\n' + raw)
    if domain == "indicators":
        for indicator in (stage / "indicators").glob("*.qml"):
            if indicator.name == "Dnd.qml":
                continue
            source = indicator.read_text()
            if "BarIndicator {" not in source:
                continue
            source = replace_once(source, "  id: root", '''  id: root
  iconComponent: Component {
    CogitatorIcons.GlyphIcon {
      text: root.text; fontFamily: root.fontFamily; color: root.foreground
    }
  }''')
            if indicator.name == "Dictation.qml":
                source = replace_once(source, '''  Process {
    command: ["bash", "-c", "omarchy-voxtype-status"]''', '''  property bool refreshStatusAfterExit: false

  Process {
    id: dictationStatus
    onExited: {
      if (root.refreshStatusAfterExit) {
        root.refreshStatusAfterExit = false
        restartDictationStatus.restart()
      }
    }
    command: ["bash", "-c", "omarchy-voxtype-status"]''')
                source = replace_once(source, '    root.bar.run("omarchy-voxtype-config")', '''    if (!dictationConfig.running) dictationConfig.running = true''')
                # Insert children before the root's closing brace. The stock
                # config helper also restarts the entire shell on exit; use
                # its terminal launcher directly and refresh only our follower.
                end = source.rfind("}")
                source = source[:end] + '''
  Timer {
    id: restartDictationStatus
    interval: 100
    onTriggered: dictationStatus.running = true
  }

  Process {
    id: dictationConfig
    command: ["omarchy-launch-floating-terminal-with-presentation", "voxtype configure"]
    onExited: {
      if (dictationStatus.running) {
        root.refreshStatusAfterExit = true
        dictationStatus.running = false
      } else {
        restartDictationStatus.restart()
      }
    }
  }
''' + source[end:]
            indicator.write_text('import "../icons" as CogitatorIcons\n' + source)
    shutil.copytree(root / "shared/icons", stage / "icons", dirs_exist_ok=True)
    return True
