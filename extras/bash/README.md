# Optional Bash prompt

This is a terminal extra, not a Quickshell widget. Core installation does not
install or activate it. It changes your interactive Bash prompt while Cogitator
is engaged and prints one machine-spirit phrase every 30 prompts.

From the project root, install it manually:

```bash
mkdir -p ~/.config/cogitator-v2/bash
install -m 0644 extras/bash/cogitator.bash ~/.config/cogitator-v2/bash/cogitator.bash
source ~/.config/cogitator-v2/bash/cogitator.bash
```

Sourcing activates it for this terminal only. For future Bash terminals, you may
add this line to your interactive Bash startup file:

```bash
[ -r ~/.config/cogitator-v2/bash/cogitator.bash ] && source ~/.config/cogitator-v2/bash/cogitator.bash
```

`cogitator_rite_disable` removes the prompt hook in the current terminal.
Disengaging Cogitator restores the captured prompt on the next prompt update.
Existing installed copies are preserved by the project cleanup.
