#!/bin/bash
# Exercises both branches of scripts/cogitator-menu with stubbed commands
# and a fake state dir. Never touches live state.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
fake=$(mktemp -d)
trap 'rm -rf "$fake"' EXIT

mkdir -p "$fake/bin" "$fake/state/cogitator-v2"
export FAKE_CALLS="$fake/calls"
printf '#!/bin/bash\nprintf "shell:%%s\\n" "$*" >> "$FAKE_CALLS"\n' > "$fake/bin/omarchy-shell"
printf '#!/bin/bash\nprintf "menu:%%s\\n" "$*" >> "$FAKE_CALLS"\n' > "$fake/bin/omarchy-menu"
chmod +x "$fake/bin/omarchy-shell" "$fake/bin/omarchy-menu"
export PATH="$fake/bin:$PATH"
export XDG_STATE_HOME="$fake/state"
router="$ROOT/scripts/cogitator-menu"

# Engaged branch: snapshot present -> console toggle.
printf '{"version":"0.2.0"}\n' > "$fake/state/cogitator-v2/snapshot.json"
"$router"
grep -q "shell:cogitator-rite toggleMenu" "$fake/calls"

# Disengaged branch: no snapshot -> stock menu.
rm "$fake/state/cogitator-v2/snapshot.json" "$fake/calls"
"$router"
grep -q "menu:toggle" "$fake/calls"

printf 'Router test passed.\n'
