#!/usr/bin/env python3
"""Settings must not redeploy/restart; palette must not add a source refresh."""
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT / "scripts/control-backend.py"))


class TransitionTests(unittest.TestCase):
    def test_disabled_effects_are_successful_noops_under_errexit(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            config = work / ".config/hypr/looknfeel.lua"
            config.parent.mkdir(parents=True)
            config.write_text("-- user configuration\n")
            script = '''source "$1/scripts/cogitator" --help >/dev/null
conf_value() { printf false; }
hyprctl() { echo unexpected-reload; return 1; }
ensure_crt_snippet
ensure_window_chamfer
echo effects-disabled-ok
'''
            env = dict(__import__("os").environ, HOME=str(work))
            result = subprocess.check_output(["bash", "-c", script, "_", str(ROOT)], env=env, text=True)
            self.assertEqual(result.strip(), "effects-disabled-ok")
            self.assertEqual(config.read_text(), "-- user configuration\n")

    def test_enable_selects_suite_without_separate_core_enable_or_quit(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            (work / ".config/omarchy/plugins/cogitator-rite/.git").mkdir(parents=True)
            (work / ".config/omarchy/plugins/cogitator-rite/.cogitator-v2-installed").write_text("owned")
            (work / ".config/omarchy/themes").mkdir(parents=True)
            script = '''source "$1/scripts/cogitator" --help >/dev/null
omarchy-shell() { printf '[{"id":"cogitator-rite"}]'; }
omarchy() { printf 'native:%s\n' "$*"; }
git() { mkdir -p "$HOME/.config/omarchy/themes/cogitator-green"; }
conf_value() { printf green; }
stamp_owned_install() { :; }
set_background_if_changed() { :; }
python3() { printf 'suite:%s\n' "${@: -1}"; }
_unit_enable
'''
            env = dict(__import__("os").environ, HOME=str(work))
            result = subprocess.check_output(["bash", "-c", script, "_", str(ROOT)], env=env, text=True)
            self.assertIn("suite:enable", result)
            self.assertNotIn("native:plugin enable", result)
            self.assertNotIn("native:restart shell", result)

    def test_ui_worker_uses_live_settings_command(self):
        globals_ = API["worker"].__globals__
        with tempfile.TemporaryDirectory() as work:
            operation = Path(work) / "operation.json"
            conf = Path(work) / "config.conf"
            conf.write_text('PALETTE="amber"\n')
            with patch.dict(globals_, {"OPERATION": operation, "CONF": conf}), patch("subprocess.run") as run:
                API["worker"]("apply", {"paletteChanged": False, "changed": ["TEXT_STREAMING"]})
                self.assertEqual(run.call_args.args[0][1:], ["settings-apply", "TEXT_STREAMING"])
                self.assertEqual(run.call_count, 1)
                self.assertEqual(json.loads(operation.read_text())["phase"], "completed")
                run.reset_mock()
                API["worker"]("apply", {"paletteChanged": True, "changed": ["PALETTE", "CRT_INTENSITY"]})
                self.assertEqual([call.args[0][1] for call in run.call_args_list], ["palette", "settings-apply"])

    def test_ordinary_settings_touch_only_config(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            (work / ".local/state/cogitator-v2").mkdir(parents=True)
            (work / ".local/state/cogitator-v2/snapshot.json").write_text("{}")
            script = '''source "$1/scripts/cogitator" --help >/dev/null
render_config_json() { printf 'config\n'; }
render_crt_frag() { printf 'shader\n'; }
ensure_crt_snippet() { printf 'crt\n'; }
ensure_window_chamfer() { printf 'corners\n'; }
omarchy() { printf 'unexpected-shell-command\n'; return 1; }
cmd_settings_apply TEXT_STREAMING
'''
            env = dict(__import__("os").environ, HOME=str(work), XDG_STATE_HOME=str(work / ".local/state"))
            result = subprocess.check_output(["bash", "-c", script, "_", str(ROOT)], env=env, text=True)
            self.assertEqual(result.splitlines(), ["config", "Settings applied live; shell kept running."])
            result = subprocess.check_output(["bash", "-c", script.replace("cmd_settings_apply TEXT_STREAMING", "cmd_settings_apply CRT_INTENSITY WINDOW_CORNER"), "_", str(ROOT)], env=env, text=True)
            self.assertEqual(result.splitlines(), ["config", "shader", "crt", "corners", "Settings applied live; shell kept running."])


if __name__ == "__main__":
    unittest.main()
