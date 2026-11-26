#!/bin/bash
# Exercises both branches of scripts/cogitator-menu with stubbed commands
# and a fake state dir. Never touches live state.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
fake=$(mktemp -d)
trap 'rm -rf "$fake"' EXIT

mkdir -p "$fake/bin" "$fake/state/cogitator-v2"
export FAKE_CALLS="$fake/calls"
cat > "$fake/bin/omarchy-shell" <<'SH'
#!/bin/bash
printf "shell:%s\n" "$*" >> "$FAKE_CALLS"
if [[ $* == "shell listPlugins" ]]; then
  [[ ${FAKE_UNAVAILABLE:-0} == 0 ]] || exit 1
  printf '[{"id":"cogitator.menu","enabled":%s},{"id":"cogitator-rite","enabled":%s}]\n' "${FAKE_ENABLED:-false}" "${FAKE_ENABLED:-false}"
fi
SH
printf '#!/bin/bash\nprintf "menu:%%s\\n" "$*" >> "$FAKE_CALLS"\n' > "$fake/bin/omarchy-menu"
chmod +x "$fake/bin/omarchy-shell" "$fake/bin/omarchy-menu"
export PATH="$fake/bin:$PATH"
export XDG_STATE_HOME="$fake/state"
router="$ROOT/scripts/cogitator-menu"

# Engaged: explicitly target the themed menu, including global search.
export FAKE_ENABLED=true
printf '{"version":"0.2.0"}\n' > "$fake/state/cogitator-v2/snapshot.json"
"$router"
grep -q 'shell:shell toggle cogitator.menu {"menu":"root"}' "$fake/calls"
! grep -q "menu:toggle" "$fake/calls"
! grep -q "cogitator-rite toggleMenu" "$fake/calls"
"$router" apps
grep -q "shell:cogitator-rite toggleLauncher" "$fake/calls"

# Disengaged branch: no snapshot -> stock menu.
rm "$fake/state/cogitator-v2/snapshot.json" "$fake/calls"
export FAKE_ENABLED=false
"$router"
grep -q "menu:toggle" "$fake/calls"
"$router" apps
grep -q "shell:omarchy.dock apps" "$fake/calls"

# A stale snapshot must not override the actual disabled plugin state.
printf '{}\n' > "$fake/state/cogitator-v2/snapshot.json"
rm "$fake/calls"
"$router"
grep -q "menu:toggle" "$fake/calls"

# An unavailable shell falls back to the default command.
export FAKE_UNAVAILABLE=1
rm "$fake/calls"
"$router"
grep -q "menu:toggle" "$fake/calls"

printf 'Router test passed.\n'
