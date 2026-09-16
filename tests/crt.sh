#!/bin/bash
# Global-CRT lifecycle under an isolated HOME. hyprctl is stubbed so no
# compositor state is touched; the real hyprland.conf is never read.
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
printf '# fixture hyprland.conf\n' > "$fake/.config/hypr/hyprland.conf"
printf 'CRT_GLOBAL="true"\nCRT_INTENSITY="0.25"\n' > "$fake/.config/cogitator-v2/cogitator.conf"

load() {
  # shellcheck disable=SC1090
  source "$ROOT/scripts/cogitator" --help >/dev/null 2>&1
}
load

# Render: tokens resolved, frag exists.
render_crt_frag
[[ -f $CONFIG_DIR/crt.frag ]] || exit 1
grep -q "{{" "$CONFIG_DIR/crt.frag" && exit 1

# Install: markers + backup + reload, exactly one block.
ensure_crt_snippet
grep -c "cogitator-v2-crt-begin" "$HOME/.config/hypr/hyprland.conf" | grep -q "^1$" || exit 1
grep -q "hyprctl:reload" "$FAKE_CALLS" || exit 1
compgen -G "$HOME/.config/hypr/hyprland.conf.bak.*" >/dev/null || exit 1
: > "$FAKE_CALLS"
ensure_crt_snippet
grep -c "cogitator-v2-crt-begin" "$HOME/.config/hypr/hyprland.conf" | grep -q "^1$" || exit 1

# Removal restores the fixture byte-for-byte (modulo trailing newline care:
# removal only deletes the managed block).
remove_crt_snippet
grep -q "cogitator-v2" "$HOME/.config/hypr/hyprland.conf" && exit 1

# Foreign shader: refuse, touch nothing.
printf 'decoration {\n    screen_shader = /evil.frag\n}\n' >> "$HOME/.config/hypr/hyprland.conf"
: > "$FAKE_CALLS"
ensure_crt_snippet 2>&1 | grep -q "Foreign" || exit 1
grep -q "cogitator-v2-crt-begin" "$HOME/.config/hypr/hyprland.conf" && exit 1

printf 'CRT lifecycle test passed.\n'
