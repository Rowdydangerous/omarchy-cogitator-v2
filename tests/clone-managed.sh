#!/bin/bash
# clone_is_managed() rules on fixtures: receipt, byte-identical content,
# foreign modification, absent dir. Never touches live config.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck disable=SC1090
source "$ROOT/scripts/cogitator" --help >/dev/null 2>&1

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# Managed by byte-identical content (no receipt file).
ours="$work/ours"
mkdir -p "$ours/components"
cp "$ROOT/overlays/notifications/NotificationCard.qml" "$ours/components/NotificationCard.qml"
printf '// cogitator-v2-herald\n' > "$ours/Service.qml"
clone_is_managed notifications "$ours" || { echo "content match should be managed" >&2; exit 1; }

# Managed by receipt alone.
receipt="$work/receipt"
mkdir -p "$receipt/components"
touch "$receipt/$HERALD_MARKER"
clone_is_managed notifications "$receipt" || { echo "receipt should be managed" >&2; exit 1; }

# Foreign: one byte differs, no receipt.
foreign="$work/foreign"
mkdir -p "$foreign/components"
cp "$ROOT/overlays/notifications/NotificationCard.qml" "$foreign/components/NotificationCard.qml"
printf '// cogitator-v2-herald\n' > "$foreign/Service.qml"
printf '\n// user tweak\n' >> "$foreign/components/NotificationCard.qml"
if clone_is_managed notifications "$foreign"; then
  echo "modified clone should be foreign" >&2
  exit 1
fi

# Absent dir.
if clone_is_managed menu "$work/nope"; then
  echo "absent dir should be unmanaged" >&2
  exit 1
fi

# Menu kind via receipt.
menurec="$work/menurec"
mkdir -p "$menurec"
touch "$menurec/$MENU_MARKER"
clone_is_managed menu "$menurec" || { echo "menu receipt should be managed" >&2; exit 1; }

printf 'Clone managed test passed.\n'
