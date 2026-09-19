#!/bin/bash
# Window-chamfer lifecycle under an isolated HOME. hyprctl is stubbed.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
fake=$(mktemp -d)
trap 'rm -rf "$fake"' EXIT

mkdir -p "$fake/bin" "$fake/.config/hypr" "$fake/.config/cogitator-v2" "$fake/.local/bin"
printf '#!/bin/bash\nprintf "hyprctl:%%s\\n" "$*" >> "$FAKE_CALLS"\n' > "$fake/bin/hyprctl"
chmod +x "$fake/bin/hyprctl"
export PATH="$fake/bin:$PATH"
export FAKE_CALLS="$fake/calls"
export HOME="$fake"
export XDG_CONFIG_HOME="$fake/.config"
export XDG_STATE_HOME="$fake/.local/state"
printf -- '-- fixture looknfeel.lua\n' > "$fake/.config/hypr/looknfeel.lua"
printf 'WINDOW_CHAMFER="true"\nWINDOW_CORNER="18"\n' > "$fake/.config/cogitator-v2/cogitator.conf"

load() {
  # shellcheck disable=SC1090
  source "$ROOT/scripts/cogitator" --help >/dev/null 2>&1
}
load
LUA="$HOME/.config/hypr/looknfeel.lua"

# Install: markers + corner value + backup + reload, exactly one block.
ensure_window_chamfer
grep -c "cogitator-v2-chamfer-begin" "$LUA" | grep -q "^1$" || exit 1
grep -q "rounding = 18" "$LUA" || exit 1
grep -q "rounding_power = 1.0" "$LUA" || exit 1
grep -q "hyprctl:reload" "$FAKE_CALLS" || exit 1
compgen -G "$LUA.bak.*" >/dev/null || exit 1
: > "$FAKE_CALLS"
ensure_window_chamfer
grep -c "cogitator-v2-chamfer-begin" "$LUA" | grep -q "^1$" || exit 1

# Disabled flag removes the block and restores the fixture.
printf 'WINDOW_CHAMFER="false"\nWINDOW_CORNER="18"\n' > "$fake/.config/cogitator-v2/cogitator.conf"
ensure_window_chamfer
grep -q "cogitator-v2" "$LUA" && exit 1
grep -q "fixture" "$LUA" || exit 1

# Out-of-range corner clamps to the default.
printf 'WINDOW_CHAMFER="true"\nWINDOW_CORNER="99"\n' > "$fake/.config/cogitator-v2/cogitator.conf"
ensure_window_chamfer
grep -q "rounding = 14" "$LUA" || exit 1

# Removal restores the fixture byte-for-byte.
remove_window_chamfer
grep -q "cogitator-v2" "$LUA" && exit 1
grep -q "fixture" "$LUA" || exit 1

printf 'Window chamfer test passed.\n'
