# Font investigation

Requirements: monospace (reliable alignment), gothic/industrial/severe, legible dense + all-caps, OFL or otherwise legally distributable. Fallback stays JetBrainsMono Nerd Font.

Findings (2026-09-14, this machine):
* `ttf-monaspace-frozen` installed, license `OFL-1.0-RFN` (pacman). Xenon variant files present (`fc-list | grep -i xenon`).
* `omarchy font list` offers Monaspace Argon/Krypton/Neon/Radon/Xenon Frozen. Xenon reads most technical/severe of the family — best v2 candidate for the machine face.
* v1 decision: NO system font change. QML uses stack `"Monaspace Xenon Frozen, JetBrainsMono Nerd Font, monospace"` so engaged surfaces render Xenon where installed and fall back cleanly elsewhere.
* Later candidates (license must be verified before bundling anything): other OFL industrial monospace families; keep a conventional code secondary if the machine font harms long-form code reading. No vendored TTF in repo until license confirmed.
