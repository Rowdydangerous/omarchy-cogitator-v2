#!/usr/bin/python3
"""Wallpaper-family generation and palette switching, using temporary homes."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SETS = runpy.run_path(str(ROOT / "scripts/palette-background.py"))


class WallpaperTests(unittest.TestCase):
    def test_packaged_defaults_match_palette_metadata_and_are_valid_images(self):
        expected = {"green": "cogitator-aquila-2560x1600.png", "amber": "mechSkull3.png",
                    "red": "mechSkull1.png", "industrial": "mechSkull2.png"}
        for palette, filename in expected.items():
            theme = ROOT if palette == "green" else ROOT / "themes" / f"cogitator-{palette}"
            self.assertEqual(SETS["default_background"](palette, theme), theme / "backgrounds" / filename)
            with Image.open(theme / "backgrounds" / filename) as image:
                self.assertEqual(image.size, (2560, 1600))
                image.verify()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / ".config"),
                        XDG_CACHE_HOME=str(self.home / ".cache"), XDG_STATE_HOME=str(self.home / ".local/state"))
        self.source = self.home / "test.png"
        Image.new("RGB", (20, 10), "white").save(self.source)
        self.original = self.source.read_bytes()

    def render(self, *args):
        return subprocess.run(["/usr/bin/python3", str(ROOT / "scripts/render-wallpaper.py"),
                               str(self.source), "--size", "320x320", *args], env=self.env,
                              capture_output=True, text=True)

    def test_default_generates_four_independent_variants_and_separate_previews(self):
        result = self.render()
        self.assertEqual(result.returncode, 0, result.stderr)
        outputs = list((self.home / ".config/omarchy/backgrounds").glob("*/*.png"))
        self.assertEqual(len(outputs), 4)
        self.assertFalse(any("-preview" in path.name for path in outputs))
        images = []
        for path in outputs:
            with Image.open(path) as image:
                self.assertEqual(image.size, (320, 320))
                images.append(image.tobytes())
        self.assertEqual(len(set(images)), 4)
        self.assertEqual(len(list((self.home / ".cache").rglob("*-preview.png"))), 4)
        self.assertFalse((self.home / ".local/state/cogitator-v2").exists())
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_collision_in_last_palette_writes_none_of_the_other_outputs(self):
        target = self.home / ".config/omarchy/backgrounds/cogitator-industrial/cogitator-test-320x320.png"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"USER FILE")
        result = self.render()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to overwrite", result.stderr)
        self.assertEqual(list((self.home / ".config/omarchy/backgrounds").glob("*/*.png")), [target])
        self.assertEqual(target.read_bytes(), b"USER FILE")

    def test_single_palette_uses_exact_output_and_custom_preview_folder(self):
        target = self.home / "my-image.png"
        preview = self.home / "previews"
        result = self.render(str(target), "--palette", "amber", "--preview-dir", str(preview))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(target.is_file())
        self.assertTrue((preview / "my-image-preview.png").is_file())
        self.assertFalse((self.home / ".config/omarchy/backgrounds").exists())

    def test_each_palette_keeps_its_choice_even_if_original_file_disappears(self):
        records = self.home / "records"
        for palette in (*SETS["PALETTES"], "custom"):
            self.source.write_bytes(palette.encode())
            SETS["remember"](palette, self.source, records)
        self.source.unlink()
        for palette in (*SETS["PALETTES"], "custom"):
            path = SETS["selected_background"](palette, self.home / "theme", records)
            self.assertEqual(path.read_bytes(), palette.encode())

    def test_first_use_defaults_do_not_create_or_overwrite_a_preference(self):
        records = self.home / "records"
        theme = ROOT / "themes/cogitator-amber"
        self.assertEqual(SETS["selected_background"]("amber", theme, records), theme / "backgrounds/mechSkull3.png")
        self.assertFalse(records.exists())
        SETS["remember"]("amber", self.source, records)
        self.assertEqual(SETS["selected_background"]("amber", theme, records).read_bytes(), self.original)

    def test_palette_command_captures_old_artwork_before_native_theme_changes_background(self):
        base = self.home / ".config/omarchy/backgrounds"
        for palette in ("green", "amber"):
            path = base / f"cogitator-{palette}/family.png"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"paired image")
        state = self.home / ".local/state"
        (state / "cogitator-v2").mkdir(parents=True)
        (state / "cogitator-v2/snapshot.json").write_text("{}")
        current = state / "omarchy/current/background"
        current.parent.mkdir(parents=True)
        current.symlink_to(base / "cogitator-green/family.png")
        (current.parent / "theme.name").write_text("cogitator-green\n")
        unrelated = self.home / "unrelated.png"
        unrelated.write_bytes(b"unrelated")
        binary = self.home / "bin/omarchy"
        binary.parent.mkdir()
        binary.write_text('''#!/bin/bash
set -eu
if [[ "$1 $2" == "theme set" ]]; then
  ln -sf "$UNRELATED" "$CURRENT"
  printf '%s' "$3" > "$(dirname "$CURRENT")/theme.name"
elif [[ "$1 $2 $3" == "theme bg set" ]]; then
  printf '%s' "$4" > "$SELECTED"
  ln -sf "$4" "$CURRENT"
fi
''')
        binary.chmod(0o755)
        env = dict(self.env, PATH=str(binary.parent) + ":" + os.environ["PATH"],
                   CURRENT=str(current), UNRELATED=str(unrelated), SELECTED=str(self.home / "selected"))
        script = '''source "$1/scripts/cogitator" --help >/dev/null
set_conf() { :; }
prepare_config() { :; }
queue_transition() { "$@"; }
cmd_palette amber
'''
        subprocess.run(["bash", "-c", script, "_", str(ROOT)], env=env, check=True, capture_output=True)
        self.assertEqual((self.home / "selected").read_text(),
                         str(self.home / ".config/omarchy/themes/cogitator-amber/backgrounds/mechSkull3.png"))
        # A same-named amber variant must NOT be automatically selected. Now
        # choose an unrelated amber wallpaper through the native selector.
        amber_choice = self.home / "user-amber.png"
        amber_choice.write_bytes(b"MY AMBER WALLPAPER")
        current.unlink()
        current.symlink_to(amber_choice)
        subprocess.run(["bash", "-c", script.replace("cmd_palette amber", "cmd_palette red"), "_", str(ROOT)],
                       env=env, check=True, capture_output=True)
        self.assertEqual((self.home / "selected").read_text(),
                         str(self.home / ".config/omarchy/themes/cogitator-red/backgrounds/mechSkull1.png"))
        amber_choice.unlink()  # Saved copy survives source/theme replacement.
        subprocess.run(["bash", "-c", script, "_", str(ROOT)], env=env, check=True, capture_output=True)
        self.assertEqual(Path((self.home / "selected").read_text()).read_bytes(), b"MY AMBER WALLPAPER")


if __name__ == "__main__":
    unittest.main()
