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
check "palette JSON" python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); assert all(k in p for k in ["background","surface","inactive","dim","normal","active","highlight","warning","critical"])' "$ROOT/palettes/green.json"
check "render reproducible" python3 "$ROOT/palettes/render.py" green --check
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
for key in ["PALETTE","CRT_ENABLED","BACKGROUND_BURN","BACKGROUND_BURN_OPACITY","TEXT_STREAMING","WORKSPACE_RITES","COGITATOR_PROP","ANIMATION_LEVEL"]:
    assert key in raw, key
' "$ROOT/config/cogitator.conf.example"
check "no system writes" bash -c '! grep -R "/usr/share/omarchy" "$1/scripts" "$1/qml" "$1/palettes" --include="*" | grep -v "Never edit"' _ "$ROOT"
check "no escaping imports" bash -c '! grep -R "\.\./\.\." "$1/qml" --include="*.qml"' _ "$ROOT"
check "marker-guarded removal" bash -c 'grep -q "owned_by_us" "$1/scripts/cogitator"' _ "$ROOT"
check "native install path" bash -c 'grep -q "omarchy plugin add" "$1/scripts/cogitator" && grep -q "git clone" "$1/scripts/cogitator"' _ "$ROOT"
check "prop is background layer" bash -c 'grep -q "WlrLayer.Bottom" "$1/qml/prop/Prop.qml" && ! grep -q "WlrLayer.Overlay" "$1/qml/prop/Prop.qml"' _ "$ROOT"

if (( failures > 0 )); then printf '%d test(s) failed.\n' "$failures" >&2; exit 1; fi
printf 'All tests passed.\n'
