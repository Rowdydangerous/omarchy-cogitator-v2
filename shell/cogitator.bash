# Opt-in Cogitator terminal rite. Inert until sourced by the operator; this
# package never edits shell startup files. Manual activation:
#   [ -r ~/.config/cogitator-v2/bash/cogitator.bash ] && source ~/.config/cogitator-v2/bash/cogitator.bash
# Installed by `cogitator enable` (as a file, never wired in). The rite only
# manifests while the snapshot exists, i.e. while the mode is engaged.
[[ $- == *i* ]] || return 0

_cogitator_state_home="${XDG_STATE_HOME:-$HOME/.local/state}"
_cogitator_snapshot="$_cogitator_state_home/cogitator-v2/snapshot.json"

_cogitator_engaged() { [[ -f $_cogitator_snapshot ]]; }

_cogitator_rites=(
  "THE MACHINE SPIRIT ACKNOWLEDGES YOUR PETITION"
  "LOCAL DATA-LOOM PURITY VERIFIED"
  "THE OMNISSIAH KNOWS ALL; COMPREHENDS ALL"
  "BLESSED IS THE MIND TOO SMALL FOR DOUBT"
  "NOOSPHERIC CARRIER REMAINS SANCTIFIED"
  "THE MOTIVE FORCE FLOWS UNIMPEDED"
  "ERROR IS HERESY; VERIFICATION IS DEVOTION"
  "YOUR DIRECTIVE ENTERS THE LITANY QUEUE"
)

if [[ -z ${_COGITATOR_RITE_INSTALLED:-} ]]; then
  _COGITATOR_ORIGINAL_PS1=${PS1-}
  _COGITATOR_RITE_INSTALLED=1
  _COGITATOR_PROMPT_COUNT=0

  _cogitator_prompt_update() {
    if _cogitator_engaged; then
      PS1="\[\e[38;2;79;208;106m\][NOOSPHERE::\h]\[\e[38;2;47;91;56m\] \u \w\n\[\e[38;2;210;255;217m\]AUTHORIZATION: ACCEPTED \[\e[38;2;79;208;106m\]> \[\e[0m\]"
      ((_COGITATOR_PROMPT_COUNT += 1))
      if (( _COGITATOR_PROMPT_COUNT % 30 == 0 )); then
        local rite_index=$(((_COGITATOR_PROMPT_COUNT / 30 - 1) % ${#_cogitator_rites[@]}))
        printf '\e[38;2;47;91;56m%s\e[0m\n' "[MACHINE SPIRIT] ${_cogitator_rites[$rite_index]}"
      fi
    else
      PS1=$_COGITATOR_ORIGINAL_PS1
    fi
  }

  cogitator_rite_disable() {
    PS1=$_COGITATOR_ORIGINAL_PS1
    if declare -p PROMPT_COMMAND 2>/dev/null | grep -q '^declare -a'; then
      local -a retained=()
      local command
      for command in "${PROMPT_COMMAND[@]}"; do
        [[ $command == _cogitator_prompt_update ]] || retained+=("$command")
      done
      PROMPT_COMMAND=("${retained[@]}")
    else
      PROMPT_COMMAND=${PROMPT_COMMAND//;_cogitator_prompt_update/}
      PROMPT_COMMAND=${PROMPT_COMMAND//_cogitator_prompt_update;/}
      [[ $PROMPT_COMMAND != _cogitator_prompt_update ]] || PROMPT_COMMAND=""
    fi
    unset _COGITATOR_RITE_INSTALLED
  }

  if declare -p PROMPT_COMMAND 2>/dev/null | grep -q '^declare -a'; then
    PROMPT_COMMAND+=("_cogitator_prompt_update")
  elif [[ -n ${PROMPT_COMMAND:-} ]]; then
    PROMPT_COMMAND="${PROMPT_COMMAND};_cogitator_prompt_update"
  else
    PROMPT_COMMAND="_cogitator_prompt_update"
  fi
  _cogitator_prompt_update
fi
