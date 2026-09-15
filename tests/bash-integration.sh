#!/bin/bash
# Sources shell/cogitator.bash in a fake HOME: engaged prompt appears iff the
# snapshot exists, and the original prompt always comes back afterwards.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
test_home=$(mktemp -d)
trap 'rm -rf "$test_home"' EXIT

mkdir -p "$test_home/.local/state/cogitator-v2"
printf '{"version":"0.2.0"}\n' > "$test_home/.local/state/cogitator-v2/snapshot.json"

HOME="$test_home" XDG_STATE_HOME="$test_home/.local/state" \
  bash --noprofile --norc -ic '
    PS1="ORIGINAL> "
    source "$1"
    _cogitator_prompt_update
    [[ $PS1 == *NOOSPHERE* ]]
    rm "$XDG_STATE_HOME/cogitator-v2/snapshot.json"
    _cogitator_prompt_update
    [[ $PS1 == "ORIGINAL> " ]]
    cogitator_rite_disable
    [[ $PS1 == "ORIGINAL> " ]]
  ' _ "$ROOT/shell/cogitator.bash"

printf 'Bash integration test passed.\n'
