#!/usr/bin/env python3
"""Check copy transformations without changing protocols, names or actions."""
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
voice = runpy.run_path(str(ROOT / "scripts/voice-style.py"))
frames = runpy.run_path(str(ROOT / "scripts/frame-style.py"))
LEXICON = json.loads((ROOT / "shared/voice/lexicon.json").read_text())


class VoiceTests(unittest.TestCase):
    def test_static_copy_preserves_predicates_and_actions(self):
        raw = '''Item {
  property string command: "Connect"
  property string selector: "Audio"
  text: state === "Connected" ? "Disconnect" : "Connect"
  onClicked: send("connect", device.name)
  // text: "Delete" is documentation, not a binding
  property string example: 'text: "Delete"'
}'''
        actual = voice["translate_source"](raw, LEXICON)
        self.assertIn('state === "Connected"', actual)
        self.assertIn('"Sever Link (Disconnect)" : "Bind Link (Connect)"', actual)
        self.assertIn('property string command: "Connect"', actual)
        self.assertIn('send("connect", device.name)', actual)
        self.assertIn('// text: "Delete"', actual)
        self.assertIn("'text: \"Delete\"'", actual)

    def test_live_names_and_user_input_are_not_translated(self):
        raw = '''Item {
  text: root.ssid
  title: root.device.name
  placeholderText: "Passphrase"
  text: root.passwordText
  text: entry.name
  text: player.trackTitle
}'''
        actual = voice["translate_source"](raw, LEXICON)
        for value in ("root.ssid", "root.device.name", "root.passwordText", "entry.name", "player.trackTitle"):
            self.assertIn(value, actual)
            self.assertNotIn("CogitatorVoice.say(" + value, actual)
        self.assertIn('placeholderText: "Access Cipher"', actual)

    def test_multiline_bindings_and_display_blocks(self):
        raw = '''Item {
  text: muted
    ? "Muted"
    : "Audio"
  text: {
    if (busy) return "Checking…"
    return root.brightnessName(percent)
  }
  font.pixelSize: 14
}'''
        actual = voice["translate_source"](raw, LEXICON)
        self.assertIn('"Vox Silenced"', actual)
        self.assertIn('"Vox Array"', actual)
        self.assertIn('CogitatorVoice.say((function() {', actual)
        self.assertIn('font.pixelSize: 14', actual)

    def test_lookup_and_profile_values_preserve_backend_contract(self):
        library = voice["voice_library"](LEXICON, json.loads((ROOT / "shared/voice/phrases.json").read_text()))
        script = library.replace(".pragma library", "") + '''
const assert = require("assert");
assert.equal(say("Audio"), "Vox Array");
assert.equal(say("Pumping power"), "Requisitioning Motive Force");
assert.equal(say("Untangling wires"), "Auxiliary Relay Awake");
assert.equal(say("Friday"), "Friday");
assert.equal(say("Office Wi-Fi"), "Office Wi-Fi");
assert.equal(say("/home/rowdy/Audio.txt"), "/home/rowdy/Audio.txt");
assert.equal(profile("balanced"), "Equilibrium");
assert.equal(profile("vendor-custom"), "vendor-custom");
assert.equal(issue(""), "");
assert.equal(issue("daemon returned error 42"), "RITE FAILED — daemon returned error 42");
'''
        subprocess.run(["node", "-e", script], check=True)

    def test_menu_names_search_aliases_and_return_contract(self):
        source = (ROOT / "overlays/rowdy.menu/Menu.qml").read_text()
        changed = voice["theme_menu"](source)
        self.assertIn('text: root.riteLabel(row).toUpperCase()', changed)
        self.assertIn('root.descriptionTextMatches(query, root.riteLabel(entry))', changed)
        self.assertIn('if (root.dmenuActive || row.appId || (entry && entry.appId)) return label', changed)
        self.assertIn('parent.provider !== "powerprofiles"', changed)
        self.assertIn('function ritePrompt()', changed)
        # Selection and execution helpers must remain byte-identical.
        for marker in ('root.deleteTarget = { appId: row.appId, label: row.label }',
                       'actionFor: function(value) { return "omarchy-font-set " + Util.shellQuote(value) }'):
            self.assertIn(marker, changed)

    def test_full_suite_packaging_and_lint_regressions(self):
        with tempfile.TemporaryDirectory() as work:
            baselines = json.loads((ROOT / "docs/stock-baseline.json").read_text())["plugins"]
            for plugin in baselines:
                stage = Path(work) / plugin["replacementId"]
                shutil.copytree(ROOT / plugin["path"], stage)
                domain = plugin["sourceId"].removeprefix("omarchy.")
                if domain == "menu":
                    shutil.copy2(ROOT / "overlays/rowdy.menu/Menu.qml", stage / "Menu.qml")
                if domain == "notifications":
                    shutil.copy2(ROOT / "overlays/notifications/NotificationCard.qml", stage / "components/NotificationCard.qml")
                frames["apply_frames"](stage)
                originals = {str(p.relative_to(stage)): p.read_bytes() for p in stage.rglob("*") if p.is_file()}
                manifest_before = json.loads((stage / "manifest.json").read_text())
                changed = voice["apply_voice"](stage)
                manifest = json.loads((stage / "manifest.json").read_text())
                self.assertEqual(manifest["id"], manifest_before["id"])
                self.assertEqual(manifest["entryPoints"], manifest_before["entryPoints"])
                self.assertEqual(manifest["omarchy"], manifest_before["omarchy"])
                self.assertTrue((stage / "voice/Lexicon.js").is_file())
                for path, original in originals.items():
                    if path.endswith(".js"):
                        self.assertEqual((stage / path).read_bytes(), original, path)
                for name in changed:
                    path = stage / name
                    content = path.read_bytes()
                    result = subprocess.run(["qmllint", "-I", "/usr/share/omarchy/shell", str(path)], capture_output=True)
                    if result.returncode:
                        path.write_bytes(originals[name])
                        before = subprocess.run(["qmllint", "-I", "/usr/share/omarchy/shell", str(path)], capture_output=True)
                        path.write_bytes(content)
                        self.assertEqual((result.returncode, result.stdout, result.stderr),
                                         (before.returncode, before.stdout, before.stderr), (domain, name, result.stderr))
            core = Path(work) / "core"
            shutil.copytree(ROOT / "qml", core)
            frames["apply_core_frames"](core)
            voice["apply_voice"](core, core=True)
            routes = (core / "menu/Routes.js").read_text()
            self.assertIn('id: "apps"', routes)
            self.assertIn('label: "Application Cogitator"', routes)
            for relative in ("menu/Menu.qml", "launcher/Launcher.qml", "prop/Prop.qml"):
                subprocess.run(["qmllint", "-I", "/usr/share/omarchy/shell", str(core / relative)], check=True)


if __name__ == "__main__":
    unittest.main()
