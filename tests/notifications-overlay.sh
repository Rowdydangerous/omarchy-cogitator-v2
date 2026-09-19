#!/bin/bash
# Herald overlay applier tests on fixture copies of the STOCK service.
# (Stock Service.qml itself is not qmllint-clean, so the gate is the
# anchor transformation + the vendored card lint, not full-file lint.)
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
APPLY="$ROOT/scripts/apply-notification-overlay.py"
CARD="$ROOT/overlays/notifications/NotificationCard.qml"

fixture=$(mktemp -d)
drift="" adopt=""
trap 'rm -rf "$fixture" ${drift:+"$drift"} ${adopt:+"$adopt"}' EXIT
mkdir -p "$fixture/components"
cp /usr/share/omarchy/shell/plugins/notifications/Service.qml "$fixture/Service.qml"

"$APPLY" "$fixture/Service.qml" "$CARD" | grep -q "herald overlay applied"
"$APPLY" "$fixture/Service.qml" "$CARD" | grep -q "already applied"
grep -q "anchors.horizontalCenter: parent.horizontalCenter" "$fixture/Service.qml"
grep -q "Layout.alignment: Qt.AlignHCenter" "$fixture/Service.qml"
cmp "$CARD" "$fixture/components/NotificationCard.qml"

# Adopt: herald-shaped but unmarked (hand-styled before management) is
# stamped, not failed.
adopt=$(mktemp -d)
mkdir -p "$adopt/components"
cp "$CARD" "$adopt/components/NotificationCard.qml"
tail -n +2 "$fixture/Service.qml" > "$adopt/Service.qml"
"$APPLY" "$adopt/Service.qml" "$CARD" | grep -q "adopted"
"$APPLY" "$adopt/Service.qml" "$CARD" | grep -q "already applied"

# Drift: stock blocks absent and no marker -> loud failure, nothing written.
drift=$(mktemp -d)
mkdir -p "$drift/components"
printf '// unrelated file\n' > "$drift/Service.qml"
if "$APPLY" "$drift/Service.qml" "$CARD" >/dev/null 2>&1; then
  echo "drift case should have failed" >&2
  exit 1
fi
test ! -e "$drift/components/NotificationCard.qml"
cmp "$drift/Service.qml" <(printf '// unrelated file\n')

printf 'Notifications overlay test passed.\n'
