#!/usr/bin/env python3
"""Presentation-only Mechanicus vocabulary; raw identifiers and data stay stock."""
import argparse
import ast
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
STRINGS = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
UI_FIELDS = re.compile(r'(?<![\w.])(?:text|label|title|subtitle|message|placeholderText|tooltipText|tooltip|promptText|cancelText|confirmText|runAgainTooltip|description|displayName)\s*:')


def expression_end(raw, start):
    """Find a QML/JS binding boundary without splitting strings or nested code."""
    depth = 0
    pos = start
    block = raw[start:start + 1] == "{"
    while pos < len(raw):
        token = STRINGS.match(raw, pos)
        if token:
            pos = token.end()
            continue
        if raw.startswith("//", pos):
            end = raw.find("\n", pos)
            if depth == 0:
                return pos
            pos = len(raw) if end < 0 else end
            continue
        char = raw[pos]
        if char in "({[":
            depth += 1
        elif char in ")}]":
            if depth == 0:
                return pos
            depth -= 1
            if block and depth == 0:
                return pos + 1
        elif depth == 0 and char in ";,":
            return pos
        elif depth == 0 and char == "\n":
            next_line = raw[pos + 1:].lstrip()
            previous = raw[start:pos].rstrip()
            continuation = next_line.startswith(("?", ":", "+", ".", "||", "&&")) or previous.endswith(("?", ":", "+", "||", "&&"))
            if not continuation:
                return pos
        pos += 1
    return pos


def literal_copy(expression, lexicon):
    def replace(token):
        before = expression[:token.start()].rstrip()
        after = expression[token.end():].lstrip()
        # Predicates, array lookup keys and switch cases remain protocol data.
        if re.search(r'(?:[=!<>]=?|\bcase|\[)\s*$', before) or (after.startswith(":") and before.endswith(("{", ","))):
            return token.group()
        try:
            value = ast.literal_eval(token.group())
        except (ValueError, SyntaxError):
            return token.group()
        replacement = lexicon.get(value)
        return json.dumps(replacement, ensure_ascii=False) if replacement is not None else token.group()
    return STRINGS.sub(replace, expression)


def translate_source(raw, lexicon, domain=""):
    changes = []
    # Mask strings/comments before finding bindings, preserving source offsets.
    protected = re.compile(STRINGS.pattern + r'|//[^\n]*|/\*[\s\S]*?\*/')
    code = protected.sub(lambda m: re.sub(r'[^\n]', ' ', m.group()), raw)
    dynamic = re.compile(r'heroStatusText|heroPhraseText|toggleHint|actionTooltip|outputVolumeName|modeLabel|brightnessName|promptText|failureMessage|authorizationLabel|dayLabel|window\.title|sectionTitle|groupTitle|wifiSectionTitle|stateLabel|statusLabel|statusText|actionStatus')
    for field in UI_FIELDS.finditer(code):
        # Ignore matches inside comments and strings (e.g. documentation).
        line_start = raw.rfind("\n", 0, field.start()) + 1
        if "//" in raw[line_start:field.start()]:
            continue
        start = field.end()
        while start < len(raw) and raw[start].isspace():
            start += 1
        end = expression_end(raw, start)
        expression = raw[start:end].rstrip()
        if not expression:
            continue
        translated = literal_copy(expression, lexicon)
        wrap = bool(dynamic.search(expression))
        if domain == "weather" and "root.label" in expression:
            wrap = True
        if domain == "agents" and "window.title" in expression:
            wrap = True
        if re.fullmatch(r'(?:root|dropbox|tailscale)\.(?:error|lastError)', expression):
            translated = f'CogitatorVoice.issue({translated})'
        elif wrap:
            if translated.startswith("{"):
                translated = f'CogitatorVoice.say((function() {translated})())'
            else:
                translated = f'CogitatorVoice.say({translated})'
        if translated != expression:
            changes.append((start, start + len(expression), translated))
    for call in re.finditer(r'\bshowTooltip\s*\(', code):
        start = call.end() - 1
        end = expression_end(raw, start)
        expression = raw[start:end]
        translated = literal_copy(expression, lexicon)
        if translated != expression:
            changes.append((start, end, translated))
    # Nested object labels can produce overlapping bindings; the outer binding
    # already covers their literals, so apply only non-overlapping spans.
    selected = []
    end = -1
    for change in sorted(changes):
        if change[0] >= end:
            selected.append(change)
            end = change[1]
    for start, end, translated in reversed(selected):
        raw = raw[:start] + translated + raw[end:]
    return raw


def voice_library(lexicon, phrases):
    lookup = dict(lexicon)
    lookup.update(phrases)
    # Status helpers may uppercase their output before it reaches the view.
    for source, target in list(lookup.items()):
        lookup.setdefault(source.upper(), target.upper())
    return '''.pragma library
// Generated from shared/voice/*.json at deployment. Display use only.
var words = ''' + json.dumps(lookup, ensure_ascii=False, indent=2) + ''';
function say(value) {
    var text = String(value === undefined || value === null ? "" : value);
    return Object.prototype.hasOwnProperty.call(words, text) ? words[text] : text;
}
function issue(value) {
    var detail = String(value || "");
    return detail ? "RITE FAILED — " + say(detail) : "";
}
function profile(value) {
    var names = {"performance": "Overdrive", "balanced": "Equilibrium",
                 "power-saver": "Conservation", "autodetect": "Adaptive"};
    return names[String(value)] || String(value);
}
function confirmation(value) {
    var text = String(value || "");
    if (text.indexOf("Uninstall ") === 0) return "Affirm Purge of Installation: " + text.slice(10);
    return say(text);
}
'''


def theme_menu(raw):
    # IDs, conditions, dmenu return values and app/provider names stay raw.
    helpers = '''
  function riteLabel(row) {
    if (!row) return "";
    var entry = root.item(String(row.itemId || row.id || ""));
    var label = String(row.label || "");
    var parent = entry ? root.item(entry.parent) : null;
    if (root.dmenuActive || row.appId || (entry && entry.appId)) return label;
    if (parent && parent.provider && parent.provider !== "powerprofiles") return label;
    var marker = label.match(/\\s*[✓✔]$/);
    var bare = marker ? label.slice(0, marker.index) : label;
    var themed = parent && parent.provider === "powerprofiles"
      ? CogitatorVoice.profile(bare) : CogitatorVoice.say(bare);
    return themed + (marker ? marker[0] : "");
  }

  function ritePrompt() {
    if (root.dmenuActive) return root.dmenuPrompt;
    var entry = root.item(root.activeMenu);
    return CogitatorVoice.say(entry ? (entry.title || entry.label) : "Issue Directive");
  }

  function riteDetail(row) {
    if (root.dmenuActive || row.appId) return row.detail;
    return String(row.detail || "").split(" › ").map(CogitatorVoice.say).join(" › ");
  }

  // Read-only diagnostic: compare the native app library with menu indexing.
  function appSearchStatus(payloadJson) {
    var payload = ({});
    try { payload = JSON.parse(payloadJson || "{}"); } catch (e) {}
    var query = String(payload.query || "");
    var library = root.appLibrary ? root.appLibrary.sortedEntries(query) : [];
    var indexed = [];
    var apps = 0;
    for (var i = 0; i < root.itemOrder.length; i++) {
      var entry = root.item(root.itemOrder[i]);
      if (!entry || entry.kind !== "app") continue;
      apps++;
      if (root.matchesQuery(entry, query)) indexed.push({id: entry.appId, name: entry.label});
    }
    var nativeEntries = DesktopEntries.applications.values;
    return JSON.stringify({hasShell: !!root.shell, hasLibrary: !!root.appLibrary,
      nativeCount: nativeEntries.length,
      nativeMatches: nativeEntries.filter(function(entry) {
        return String(entry.name).toLowerCase().indexOf(query.toLowerCase()) !== -1;
      }).map(function(entry) { return {id: entry.id, name: entry.name}; }),
      activeMenu: root.activeMenu, filter: root.filterText,
      appsLoaded: !!root.providersLoaded["apps"], indexedCount: apps,
      library: library.map(function(row) { return {id: row.entry.id, name: row.entry.name}; }),
      indexed: indexed});
  }
'''
    raw = raw.replace("  function depthFor(id) {", helpers + "\n  function depthFor(id) {", 1)
    raw = raw.replace("return MenuModel.matchesQuery(entry, query, root.isVisible(entry))",
                      "return MenuModel.matchesQuery(entry, query, root.isVisible(entry))\n"
                      "      || (root.isVisible(entry) && root.descriptionTextMatches(query, root.riteLabel(entry)))", 1)
    raw = raw.replace("text: row.label.toUpperCase()", "text: root.riteLabel(row).toUpperCase()", 1)
    raw = raw.replace("text: row.detail", "text: root.riteDetail(row)", 1)
    raw = re.sub(r'text: \(root\.filterText \|\| \(root\.dmenuActive[^\n]+\.toUpperCase\(\)',
                 'text: (root.filterText || (root.ritePrompt() + "…")).toUpperCase()', raw, count=1)
    return raw


def apply_voice(stage, root=ROOT, core=False):
    directory = root / "shared/voice"
    if not (directory / "lexicon.json").exists():
        return []
    lexicon = json.loads((directory / "lexicon.json").read_text())
    phrases = json.loads((directory / "phrases.json").read_text())
    manifest_path = stage / "manifest.json"
    domain = "core"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        domain = manifest["id"].removeprefix("cogitator.")
        names = json.loads((directory / "plugin-names.json").read_text())
        if domain in names:
            manifest["name"] = "Cogitator " + names[domain]
            if "barWidget" in manifest:
                manifest["barWidget"]["displayName"] = names[domain]
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    changed = []
    for file in list(stage.rglob("*.qml")) + (list(stage.rglob("Routes.js")) if core else []):
        original = file.read_text()
        translated = translate_source(original, lexicon, domain)
        if domain == "menu" and file.name == "Menu.qml":
            translated = theme_menu(translated)
        if file.name == "ConfirmDialog.qml":
            translated = translated.replace("text: root.message", "text: CogitatorVoice.confirmation(root.message)")
        if domain == "power" and file.name == "Panel.qml":
            translated = translated.replace('text: String(modelData).charAt(0).toUpperCase() + String(modelData).slice(1)',
                                            'text: CogitatorVoice.profile(modelData)')
        if translated != original:
            if file.suffix == ".qml" and "CogitatorVoice." in translated:
                relative = Path("voice/Lexicon.js") if file.parent == stage else Path(*([".."] * len(file.parent.relative_to(stage).parts))) / "voice/Lexicon.js"
                translated = f'import "{relative.as_posix()}" as CogitatorVoice\n' + translated
            file.write_text(translated)
            changed.append(str(file.relative_to(stage)))
    (stage / "voice").mkdir(exist_ok=True)
    (stage / "voice/Lexicon.js").write_text(voice_library(lexicon, phrases))
    return changed


def inventory(root=ROOT):
    groups = {}
    for folder in ("plugins", "shared/frames", "qml", "overlays"):
        for file in sorted((root / folder).rglob("*")):
            if file.suffix not in (".qml", ".js"):
                continue
            for number, line in enumerate(file.read_text().splitlines(), 1):
                if line.lstrip().startswith("//"):
                    continue
                for token in STRINGS.finditer(line):
                    raw = token.group()
                    value = raw[1:-1]
                    if not re.search(r'[A-Za-z]{3}', value) or re.search(r'[/\\]|^#[0-9a-fA-F]+$', value):
                        continue
                    if UI_FIELDS.search(line[:token.start()]):
                        role = "display"
                    elif re.search(r'return\s|showTooltip\(|tooltip|[Hh]int|[Ee]rror|[Ss]tatus|prompt', line):
                        role = "review"
                    else:
                        continue
                    groups.setdefault(value, []).append({"file": str(file.relative_to(root)), "line": number,
                                                         "role": role, "context": line.strip()})
    return groups


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["inventory"])
    parser.parse_args()
    groups = inventory()
    (ROOT / "docs/voice-inventory.json").write_text(json.dumps(groups, indent=2) + "\n")
    for value, locations in sorted(groups.items()):
        first = locations[0]
        print(f'{value} [{first["file"]}:{first["line"]}]')
