#!/bin/bash
# Regression suite. Read-only except temp dirs.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
failures=0
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then printf 'PASS: %s\n' "$label"
  else printf 'FAIL: %s\n' "$label" >&2; failures=$((failures + 1)); fi
}

check "manager syntax" bash -n "$ROOT/scripts/cogitator"
check "bash rite syntax" bash -n "$ROOT/shell/cogitator.bash"
check "bash integration" "$ROOT/tests/bash-integration.sh"
check "menu router" "$ROOT/tests/router.sh"
check "clone managed rules" "$ROOT/tests/clone-managed.sh"
check "notifications overlay" "$ROOT/tests/notifications-overlay.sh"
check "menu overlay vendored" bash -c 'grep -q "redirectApps" "$1/overlays/rowdy.menu/Menu.qml" && grep -q "escapeToNexus" "$1/overlays/rowdy.menu/Menu.qml" && grep -q ": 560)" "$1/overlays/rowdy.menu/Menu.qml"' _ "$ROOT"
check "menu overlay lint" qmllint -I /usr/share/omarchy/shell "$ROOT/overlays/rowdy.menu/Menu.qml"
check "nexus filter + commit keys" bash -c 'grep -q "onRightPressed" "$1/qml/menu/Menu.qml" && grep -q "appendFilter" "$1/qml/menu/Menu.qml" && grep -q "TYPE TO FILTER // RIGHT TO COMMIT" "$1/qml/menu/Menu.qml"' _ "$ROOT"
check "chamfer frames" bash -c 'grep -q "card.width - root.chamfer\|card.width - 30" "$1/qml/menu/Menu.qml" "$1/qml/launcher/Launcher.qml" && grep -q "QtQuick.Shapes" "$1/qml/menu/Menu.qml" "$1/qml/launcher/Launcher.qml"' _ "$ROOT"
check "unified 560 width" bash -c 'grep -q "Math.min(560" "$1/qml/menu/Menu.qml" "$1/qml/launcher/Launcher.qml"' _ "$ROOT"
check "clone lifecycle wiring" bash -c 'grep -q "ensure_menu_overlay" "$1/scripts/cogitator" && grep -q "restore_menu_overlay" "$1/scripts/cogitator" && grep -q "menuClone" "$1/scripts/cogitator"' _ "$ROOT"
check "global CRT lifecycle" "$ROOT/tests/crt.sh"
check "window chamfer" "$ROOT/tests/window-chamfer.sh"
check "configure no-change" bash -c 'EDITOR=true "$1/scripts/cogitator" configure | grep -q "No changes"' _ "$ROOT"
check "palette JSON" python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); assert all(k in p for k in ["background","surface","inactive","dim","normal","active","highlight","warning","critical"])' "$ROOT/palettes/green.json"
check "render reproducible" bash -c '"$1/palettes/render.py" green amber red industrial --check' _ "$ROOT"
check "palette JSONs" bash -c 'for p in amber red industrial; do python3 -c "import json,sys; p=json.load(open(sys.argv[1])); assert all(k in p for k in [\"background\",\"surface\",\"inactive\",\"dim\",\"normal\",\"active\",\"highlight\",\"warning\",\"critical\"])" "$1/palettes/$p.json" || exit 1; done' _ "$ROOT"
check "palette rejects unknown" bash -c '"$1/scripts/cogitator" palette bogus 2>&1 | grep -q usage' _ "$ROOT"
check "custom render" bash -c '"$1/palettes/render.py" custom --phosphor "#7CFF6B" && python3 -c "import tomllib; tomllib.load(open(\"$1/themes/cogitator-custom/colors.toml\",\"rb\"))" _ "$1"; status=$?; rm -rf "$1/themes/cogitator-custom"; exit $status' _ "$ROOT"
check "colors TOML" python3 -c 'import tomllib,sys; tomllib.load(open(sys.argv[1],"rb"))' "$ROOT/colors.toml"
check "shell TOML" python3 -c 'import tomllib,sys; tomllib.load(open(sys.argv[1],"rb"))' "$ROOT/shell.toml"
check "manifest JSON" python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); assert m["id"]=="cogitator-rite" and "service" in m["kinds"]' "$ROOT/manifest.json"
check "manifest contract" omarchy plugin validate "$ROOT"
check "native plugin layout" bash -c 'test -f "$1/manifest.json" && test -f "$1/qml/Service.qml"' _ "$ROOT"
check "native theme layout" bash -c 'test -f "$1/colors.toml" && test -f "$1/shell.toml" && test -s "$1/backgrounds/cogitator-green-grid.png" && test -s "$1/icons.theme"' _ "$ROOT"
check "QML syntax" qmllint -I /usr/share/omarchy/shell "$ROOT/qml/Service.qml" "$ROOT/qml/prop/Prop.qml" "$ROOT/qml/burn/Burn.qml" "$ROOT/qml/fx/Crt.qml"
check "status read-only" bash -c '"$1/scripts/cogitator" status | grep -q THEME' _ "$ROOT"
check "config example parses" python3 -c '
import sys
raw = {}
for line in open(sys.argv[1]):
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    raw[k.strip()] = v.strip().strip("\"")
for key in ["PALETTE","CRT_ENABLED","CRT_GLOBAL","CRT_INTENSITY","WINDOW_CHAMFER","WINDOW_CORNER","FLICKER","NOISE","PERSISTENCE","GHOSTING","SCREEN_BURN","BRIGHTNESS_FALLOFF","BACKGROUND_BURN","BACKGROUND_BURN_OPACITY","TEXT_STREAMING","WORKSPACE_RITES","COGITATOR_PROP","ANIMATION_LEVEL"]:
    assert key in raw, key
' "$ROOT/config/cogitator.conf.example"
check "no system writes" bash -c '! grep -R "/usr/share/omarchy" "$1/scripts" "$1/qml" "$1/palettes" --include="*" | grep -v "Never edit" | grep -v "OMARCHY_PATH:-"' _ "$ROOT"
check "no escaping imports" bash -c '! grep -R "\.\./\.\." "$1/qml" --include="*.qml"' _ "$ROOT"
check "marker-guarded removal" bash -c 'grep -q "owned_by_us" "$1/scripts/cogitator"' _ "$ROOT"
check "native install path" bash -c 'grep -q "omarchy plugin add" "$1/scripts/cogitator" && grep -q "git clone" "$1/scripts/cogitator"' _ "$ROOT"
check "prop is background layer" bash -c 'grep -q "WlrLayer.Bottom" "$1/qml/prop/Prop.qml" && ! grep -q "WlrLayer.Overlay" "$1/qml/prop/Prop.qml"' _ "$ROOT"

if (( failures > 0 )); then printf '%d test(s) failed.\n' "$failures" >&2; exit 1; fi
printf 'All tests passed.\n'
