#!/usr/bin/env python3
"""Validate standalone frame packaging, local imports and preserved card APIs."""
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
styler = runpy.run_path(str(ROOT / "scripts/frame-style.py"))
apply_frames = styler["apply_frames"]
expected = {"audio", "agents", "bluetooth", "clock", "dropbox", "monitor", "network",
            "power", "tailscale", "weather", "tray", "media", "clipboard", "emojis",
            "osd", "reminders", "polkit", "lock", "image-picker", "wifiqr",
            "speedtest", "disk-speedtest", "menu", "notifications", "bar"}
with tempfile.TemporaryDirectory() as work:
    styled_plugins = set()
    upstream_lint_limits = []
    for plugin in sorted(expected):
        stage = Path(work) / plugin
        shutil.copytree(ROOT / "plugins" / plugin, stage)
        if plugin == "menu":
            shutil.copy2(ROOT / "overlays/rowdy.menu/Menu.qml", stage / "Menu.qml")
        if plugin == "notifications":
            shutil.copy2(ROOT / "overlays/notifications/NotificationCard.qml", stage / "components/NotificationCard.qml")
        originals = {str(p.relative_to(stage)): p.read_text() for p in stage.rglob("*.qml")}
        changed = apply_frames(stage)
        assert changed, f"No frame applied to {plugin}"
        styled_plugins.add(plugin)
        assert (stage / "frames/FrameSurface.qml").is_file()
        for name in changed:
            content = (stage / name).read_text()
            assert "as CogitatorFrames" in content
            # Resolve the generated import relative to the actual QML file.
            relative = content.split('import "', 1)[1].split('"', 1)[0]
            assert ((stage / name).parent / relative / "FrameSurface.qml").is_file()
            command = ["qmllint", "-I", "/usr/share/omarchy/shell", str(stage / name)]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode:
                # Some unchanged stock panels return 255 without diagnostics.
                # Compare the same file's original version, not a different
                # import context, and reject any new diagnostics/failure.
                (stage / name).write_text(originals[name])
                baseline = subprocess.run(command, capture_output=True, text=True)
                (stage / name).write_text(content)
                assert result.returncode == baseline.returncode and result.stderr == baseline.stderr and result.stdout == baseline.stdout, (plugin, name, result.stderr)
                upstream_lint_limits.append(f"{plugin}/{name}")
        if plugin == "lock":
            assert "onAccepted" in (stage / "LockView.qml").read_text()
    assert styled_plugins == expected
    core = Path(work) / "core"
    shutil.copytree(ROOT / "qml", core)
    styler["apply_core_frames"](core)
    for relative in ("menu/Menu.qml", "launcher/Launcher.qml", "prop/Prop.qml"):
        assert "CogitatorFrames.FrameSurface" in (core / relative).read_text()
        subprocess.run(["qmllint", "-I", "/usr/share/omarchy/shell", str(core / relative)], check=True)
shared = ROOT / "shared/frames"
for file in shared.glob("*.qml"):
    subprocess.run(["qmllint", "-I", "/usr/share/omarchy/shell", str(file)], check=True)
keyboard = (shared / "KeyboardPanel.qml").read_text()
assert "focusTarget" in keyboard and "onBackingWindowVisibleChanged" in keyboard
assert "HyprlandFocusGrab" in (shared / "PopupCard.qml").read_text()
assert "function handleKey" in (shared / "ConfirmDialog.qml").read_text()
print(f"Shared frames packaged for {len(expected)} plugin surfaces; QML lint passed.")
if upstream_lint_limits:
    print("Existing upstream lint limitations (unchanged diagnostics): " + ", ".join(upstream_lint_limits))
