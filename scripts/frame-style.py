#!/usr/bin/env python3
"""Package shared frame chrome into each installed plugin, retaining stock logic."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
HOST_TYPES = ("KeyboardPanel", "PopupCard", "ConfirmDialog", "SpeedTestOverlay", "PanelToolTip")


def import_host_frames():
    """One-time pinned copy. Refuse to overwrite reviewed component sources."""
    directory = ROOT / "shared/frames"
    records = {}
    for name in HOST_TYPES:
        target = directory / f"{name}.qml"
        if target.exists():
            raise RuntimeError(f"Existing frame component preserved: {target}")
        source = Path("/usr/share/omarchy/shell/Ui") / target.name
        raw = source.read_text()
        records[name] = hashlib.sha256(source.read_bytes()).hexdigest()
        if "import qs.Ui" not in raw:
            raw = "import qs.Ui\n" + raw
        if name == "SpeedTestOverlay":
            raw = raw.replace("Item {\n      id: cluster", "FrameSurface {\n      id: cluster")
            raw = raw.replace("width: content.implicitWidth", "width: content.implicitWidth + 40")
            raw = raw.replace("height: content.implicitHeight", "height: content.implicitHeight + 40")
            raw = raw.replace("id: content\n        anchors.fill: parent", "id: content\n        anchors.fill: parent\n        anchors.margins: 20")
        else:
            raw = raw.replace("BorderSurface {", "FrameSurface {", 1)
        if name == "PopupCard":
            raw = raw.replace("implicitWidth: contentWidth", "implicitWidth: contentWidth + 12")
            raw = raw.replace("implicitHeight: contentHeight", "implicitHeight: contentHeight + 12")
            raw = raw.replace("id: card\n    anchors.fill: parent", "id: card\n    anchors.fill: parent\n    anchors.margins: 6")
        if name == "PanelToolTip":
            raw = raw.replace("padding: 0", "padding: 6", 1)
            raw = raw.replace("background: FrameSurface {", "background: FrameSurface {\n    x: 6; y: 6\n    width: root.width - 12; height: root.height - 12")
        target.write_text(raw)
    (directory / "upstream.json").write_text(json.dumps(records, indent=2) + "\n")


def apply_frames(stage, root=ROOT):
    shared = root / "shared/frames"
    if not shared.exists():
        return []
    name = stage.name
    manifest = stage / "manifest.json"
    if manifest.exists():
        name = json.loads(manifest.read_text())["id"].removeprefix("cogitator.")
    changed = []
    for file in list(stage.rglob("*.qml")):
        raw = file.read_text()
        styled = re.sub(r"(?<![\w.])(" + "|".join(HOST_TYPES) + r")\s*\{", r"CogitatorFrames.\1 {", raw)
        # Only outer cards: do not turn sliders, buttons and list rows into frames.
        if name in ("clipboard", "emojis", "osd", "reminders", "polkit", "lock"):
            styled = re.sub(r"\bBorderSurface\s*\{", "CogitatorFrames.FrameSurface {", styled, count=1)
            if name == "lock" and file.name == "LockView.qml":
                styled = styled.replace("radius: Style.cornerRadius\n      clip: true", "radius: 0\n      clip: false", 1)
        elif name in ("menu", "notifications"):
            # Their existing outline/brackets stay; replace the rectangular fill.
            styled = re.sub(r"\bBorderSurface\s*\{", "CogitatorFrames.FrameSurface {\n  drawOutline: false\n  drawFlares: false", styled, count=1)
        elif name == "image-picker":
            styled = styled.replace("Item {\n      id: card", "CogitatorFrames.FrameSurface {\n      id: card")
        elif name == "wifiqr":
            styled = styled.replace("Item {\n        anchors.centerIn: parent\n        width: content.implicitWidth",
                                    "CogitatorFrames.FrameSurface {\n        anchors.centerIn: parent\n        width: content.implicitWidth + 40")
            styled = styled.replace("height: content.implicitHeight", "height: content.implicitHeight + 40")
            styled = styled.replace("id: content\n          anchors.fill: parent", "id: content\n          anchors.fill: parent\n          anchors.margins: 20")
        elif name == "bar":
            styled = styled.replace("BorderSurface {\n        id: tooltipBubble", "CogitatorFrames.FrameSurface {\n        id: tooltipBubble\n        x: 6; y: 6")
            styled = styled.replace("Math.ceil(tooltipBubble.implicitWidth)", "Math.ceil(tooltipBubble.implicitWidth) + 12")
            styled = styled.replace("Math.ceil(tooltipBubble.implicitHeight)", "Math.ceil(tooltipBubble.implicitHeight) + 12")
        if styled != raw:
            relative = Path("frames") if file.parent == stage else Path(*([".."] * len(file.parent.relative_to(stage).parts))) / "frames"
            styled = f'import "{relative.as_posix()}" as CogitatorFrames\n' + styled
            file.write_text(styled)
            changed.append(str(file.relative_to(stage)))
    if changed:
        shutil.copytree(shared, stage / "frames", dirs_exist_ok=True)
    return changed


def apply_core_frames(stage, root=ROOT):
    if not (root / "shared/frames").exists():
        return
    changed = False
    for relative in ("menu/Menu.qml", "launcher/Launcher.qml"):
        file = stage / relative
        if not file.exists():
            continue
        raw = file.read_text()
        styled = re.sub(r"Rectangle \{\n(\s*)id: card\b",
                        r"CogitatorFrames.FrameSurface {\n\1drawOutline: false\n\1drawFlares: false\n\1id: card", raw, count=1)
        styled = styled.replace("border.width: 0", "// Outline is drawn by the reference frame below.", 1)
        if styled != raw:
            file.write_text('import "../frames" as CogitatorFrames\n' + styled)
            changed = True
    file = stage / "prop/Prop.qml"
    if file.exists():
        raw = file.read_text()
        styled = raw.replace("Rectangle {\n                    anchors.fill: parent\n                    color: Qt.rgba(root.abyss",
                             "CogitatorFrames.FrameSurface {\n                    outlineColor: root.phosphor\n                    anchors.fill: parent\n                    color: Qt.rgba(root.abyss", 1)
        styled = styled.replace("                    border.color: root.dim\n                    border.width: 1\n", "", 1)
        inner = '''                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 5
                    color: "transparent"
                    border.color: Qt.rgba(root.phosphor.r, root.phosphor.g, root.phosphor.b, 0.35)
                    border.width: 1
                }'''
        styled = styled.replace(inner, "")
        if styled != raw:
            file.write_text('import "../frames" as CogitatorFrames\n' + styled)
            changed = True
    if changed:
        shutil.copytree(root / "shared/frames", stage / "frames", dirs_exist_ok=True)


if __name__ == "__main__":
    import_host_frames()
