#!/usr/bin/env python3
"""Check native icon states, packaging, and unchanged interaction contracts."""
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
apply_icons = runpy.run_path(str(ROOT / "scripts/icon-style.py"))["apply_icons"]
frames = runpy.run_path(str(ROOT / "scripts/frame-style.py"))["apply_frames"]
voice = runpy.run_path(str(ROOT / "scripts/voice-style.py"))["apply_voice"]


class IconTests(unittest.TestCase):
    def test_state_thresholds_and_invalid_measurements(self):
        model = (ROOT / "shared/icons/IconState.js").read_text().replace(".pragma library", "")
        script = model + '''
const assert = require("assert");
assert.deepEqual([0, .1, .34, .67, 1.5].map(volumeBands), [0, 1, 2, 3, 3]);
assert.deepEqual([-1, 0, 20, 21, 40, 60, 80, 100].map(signalBands), [0, 0, 0, 1, 1, 2, 3, 4]);
assert.equal(signalBands(NaN), 0);
assert.deepEqual([-.5, 0, .1, .5, 1, 2].map(cellCharge), [0, 0, .1, .5, 1, 1]);
assert.equal(cellCharge(NaN), 0);
assert.equal(weatherKind(""), "sun");
assert.equal(weatherKind(""), "moon");
assert.equal(weatherKind(""), "rain");
assert.equal(weatherKind(""), "snow");
assert.equal(weatherKind(""), "storm");
assert.equal(weatherKind("invalid"), "unknown");
'''
        subprocess.run(["node", "-e", script], check=True)

    def test_packaged_icons_keep_models_and_actions(self):
        with tempfile.TemporaryDirectory() as work:
            for domain, handlers in {
                "audio": ["root.toggleAllMuted()", "root.setOutputVolume(root.outputVolume + wheel.steps * 0.05)"],
                "network": ["if (root.opened) root.close()", "else root.open()"],
                "power": ["root.togglePercentage()", "else root.toggle()"]
            }.items():
                stage = Path(work) / domain
                shutil.copytree(ROOT / "plugins" / domain, stage)
                model = (stage / "Model.js").read_bytes()
                original_panel = (stage / "Panel.qml").read_text()
                self.assertTrue(apply_icons(stage))
                source = (stage / "Panel.qml").read_text()
                self.assertEqual((stage / "Model.js").read_bytes(), model)
                for handler in handlers:
                    self.assertIn(handler, source)
                self.assertIn("tooltipText:", source)
                self.assertTrue((stage / "icons/IconState.js").is_file())
                # Match the suite's existing stock-panel lint regression check.
                # The Qt 6 analyzer can loop on these host-scoped panel types;
                # analyze the standalone icon components separately below.
                command = ["qmllint", "-I", "/usr/share/omarchy/shell", str(stage / "Panel.qml")]
                result = subprocess.run(command, capture_output=True, timeout=15)
                if result.returncode:
                    (stage / "Panel.qml").write_text(original_panel)
                    baseline = subprocess.run(command, capture_output=True, timeout=15)
                    (stage / "Panel.qml").write_text(source)
                    self.assertEqual((result.returncode, result.stdout, result.stderr),
                                     (baseline.returncode, baseline.stdout, baseline.stderr))
            for icon in (ROOT / "shared/icons").glob("*.qml"):
                source = icon.read_text()
                self.assertNotIn("MultiEffect", source)
                self.assertNotIn("Image {", source)
                self.assertNotIn("layer.enabled", source)
                subprocess.run(["/usr/lib/qt6/bin/qmllint", "--ignore-settings", "--silent", str(icon)], check=True, timeout=15)

    def test_remaining_icons_after_frame_and_voice_packaging(self):
        with tempfile.TemporaryDirectory() as work:
            cases = {
                "bluetooth": ("Panel.qml", "root.toggleBluetooth()"),
                "monitor": ("Panel.qml", "root.setBrightness(root.brightnessPercent + wheel.steps * 5)"),
                "microphone": ("Microphone.qml", "root.toggleMute()"),
                "system-update": ("SystemUpdate.qml", "root.runUpdate()"),
                "weather": ("BarWidget.qml", "root.togglePanel()"),
                "indicators": ("indicators/Dnd.qml", "root.notificationService.setDoNotDisturb(!root.notificationService.doNotDisturb)"),
                "clipboard": ("Clipboard.qml", "root.filterText"),
                "clock": ("Panel.qml", "root.goToToday()"),
                "agents": ("Panel.qml", "root.launchAgent()")
            }
            for domain, (filename, handler) in cases.items():
                stage = Path(work) / domain
                shutil.copytree(ROOT / "plugins" / domain, stage)
                frames(stage)
                if domain == "weather":
                    runpy.run_path(str(ROOT / "scripts/layout-style.py"))["weather_layout"](stage / "Panel.qml")
                voice(stage)
                original_models = {p: p.read_bytes() for p in stage.rglob("*.js")}
                file = stage / filename
                original = file.read_text()
                self.assertTrue(apply_icons(stage))
                if domain == "weather":
                    layout = (stage / "Panel.qml").read_text()
                    self.assertNotIn("width: weatherStats.implicitWidth", layout)
                    self.assertNotIn("height: Math.max(heroLeft.height, heroRight.height)", layout)
                    self.assertIn("width: (weatherStats.width - weatherStats.spacing * 2) / 3", layout)
                    self.assertIn('text: "THERMAL FEEL"', layout)
                if domain == "indicators":
                    for name in ("StayAwake", "NightLight", "Dictation", "ScreenRecording", "Reminder"):
                        self.assertIn("CogitatorIcons.GlyphIcon", (stage / f"indicators/{name}.qml").read_text())
                    dictation = (stage / "indicators/Dictation.qml").read_text()
                    self.assertNotIn('root.bar.run("omarchy-voxtype-config")', dictation)
                    self.assertNotIn("restart-shell", dictation)
                    self.assertIn('["omarchy-launch-floating-terminal-with-presentation", "voxtype configure"]', dictation)
                    self.assertIn('id: dictationStatus', dictation)
                    self.assertIn('dictationStatus.running = false', dictation)
                    self.assertIn('onTriggered: dictationStatus.running = true', dictation)
                    self.assertIn('if (!dictationConfig.running)', dictation)
                    subprocess.run(["/usr/lib/qt6/bin/qmllint", "--ignore-settings", "--silent",
                                    str(stage / "indicators/Dictation.qml")], check=True, timeout=15)
                content = file.read_text()
                self.assertIn(handler, content)
                for path, data in original_models.items():
                    self.assertEqual(path.read_bytes(), data)
                relative = "../icons" if domain == "indicators" else "icons"
                self.assertIn(f'import "{relative}" as CogitatorIcons', content)
                command = ["qmllint", "-I", "/usr/share/omarchy/shell", str(file)]
                result = subprocess.run(command, capture_output=True, timeout=15)
                if result.returncode:
                    file.write_text(original)
                    baseline = subprocess.run(command, capture_output=True, timeout=15)
                    file.write_text(content)
                    self.assertEqual((result.returncode, result.stdout, result.stderr),
                                     (baseline.returncode, baseline.stdout, baseline.stderr), domain)

    def test_drift_is_detected_instead_of_partial_icon_replacement(self):
        with tempfile.TemporaryDirectory() as work:
            stage = Path(work)
            shutil.copytree(ROOT / "plugins/audio", stage, dirs_exist_ok=True)
            panel = stage / "Panel.qml"
            panel.write_text(panel.read_text().replace("text: root.outputIcon()", "text: changedUpstream()"))
            with self.assertRaises(RuntimeError):
                apply_icons(stage)


if __name__ == "__main__":
    unittest.main()
