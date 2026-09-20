#!/bin/bash
# restore_* discovery paths with stubbed omarchy commands and a fixture
# HOME. Covers the real bug: snapshot predates the clone (empty clone_id)
# yet a managed clone lingers while disengaged. Never touches live config.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin" "$work/home/.config/omarchy/plugins"

cat > "$work/bin/omarchy-shell" <<EOF
#!/bin/bash
cat "\$FIXTURE_PLUGINS_JSON"
EOF
cat > "$work/bin/omarchy" <<'EOF'
#!/bin/bash
# stub: omarchy plugin remove <id> --yes  -> delete fixture clone dir, log it
echo "omarchy $*" >> "$FIXTURE_CALL_LOG"
if [[ "$1" == "plugin" && "$2" == "remove" ]]; then
  rm -rf "$FIXTURE_HOME/.config/omarchy/plugins/$3"
fi
EOF
chmod +x "$work/bin/omarchy-shell" "$work/bin/omarchy"
export PATH="$work/bin:$PATH"
export FIXTURE_CALL_LOG="$work/calls"
export FIXTURE_HOME="$work/home"
export HOME="$work/home"
: > "$FIXTURE_CALL_LOG"

# shellcheck disable=SC1090
source "$ROOT/scripts/cogitator" --help >/dev/null 2>&1

plugins_json() {
  printf '%s' "$1" > "$work/plugins.json"
  export FIXTURE_PLUGINS_JSON="$work/plugins.json"
}
blendir() { printf '%s/.config/omarchy/plugins/%s' "$FIXTURE_HOME" "$1"; }

# Case 1: menu clone, content-identical, no receipt, empty snapshot id.
plugins_json '[{"id":"rowdy.menu","clonedFrom":"omarchy.menu"}]'
mkdir -p "$(blendir rowdy.menu)"
cp "$ROOT/overlays/rowdy.menu/Menu.qml" "$(blendir rowdy.menu)/Menu.qml"
restore_menu_overlay "" ""
[[ ! -e $(blendir rowdy.menu) ]] || { echo "managed menu clone should be removed" >&2; exit 1; }
grep -q "plugin remove rowdy.menu" "$FIXTURE_CALL_LOG" || { echo "remove not invoked" >&2; exit 1; }

# Case 2: foreign content stays put.
plugins_json '[{"id":"rowdy.menu","clonedFrom":"omarchy.menu"}]'
mkdir -p "$(blendir rowdy.menu)"
cp "$ROOT/overlays/rowdy.menu/Menu.qml" "$(blendir rowdy.menu)/Menu.qml"
printf '\n// user hand-tweak\n' >> "$(blendir rowdy.menu)/Menu.qml"
: > "$FIXTURE_CALL_LOG"
restore_menu_overlay "" ""
[[ -d $(blendir rowdy.menu) ]] || { echo "foreign clone must be left alone" >&2; exit 1; }
grep -q "plugin remove" "$FIXTURE_CALL_LOG" && { echo "foreign clone must not be removed" >&2; exit 1; }

# Case 3: herald discovery removal (card identical + marker line in Service).
plugins_json '[{"id":"rowdy.notifications","clonedFrom":"omarchy.notifications"}]'
mkdir -p "$(blendir rowdy.notifications)/components"
cp "$ROOT/overlays/notifications/NotificationCard.qml" "$(blendir rowdy.notifications)/components/NotificationCard.qml"
printf '// cogitator-v2-herald\n' > "$(blendir rowdy.notifications)/Service.qml"
: > "$FIXTURE_CALL_LOG"
restore_herald "" ""
[[ ! -e $(blendir rowdy.notifications) ]] || { echo "managed herald clone should be removed" >&2; exit 1; }

# Case 4: backup present but clone dir gone -> warn, exit 0 (never fail disable).
mkdir -p "$work/backup"
printf '// backed up\n' > "$work/backup/Menu.qml"
restore_menu_overlay "ghost.menu" "$work/backup" || { echo "missing clone must not fail" >&2; exit 1; }

printf 'Clone restore test passed.\n'
