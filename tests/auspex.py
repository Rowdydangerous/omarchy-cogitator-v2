#!/usr/bin/env python3
"""Read-only telemetry and real QML observation/typing behavior, offscreen."""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = runpy.run_path(str(ROOT / "qml/prop/stats.py"))["snapshot"]
EXPRESSION_END = runpy.run_path(str(ROOT / "scripts/voice-style.py"))["expression_end"]


class TelemetryTests(unittest.TestCase):
    def test_cpu_counters_memory_and_uptime_from_fixtures(self):
        with tempfile.TemporaryDirectory() as work:
            proc = Path(work)
            (proc / "stat").write_text("cpu 100 2 50 800 20 3 5 0 10 1\n")
            (proc / "meminfo").write_text("MemTotal: 1000 kB\nMemAvailable: 600 kB\n")
            (proc / "uptime").write_text("1234.5 2000\n")
            with patch("os.statvfs", side_effect=OSError("fixture unavailable")):
                record = SNAPSHOT(proc)
            self.assertEqual(record["cpu"], {"idle": 820, "total": 980})
            self.assertEqual(record["memory"]["percent"], 40)
            self.assertEqual(record["uptime"], 1234.5)
            self.assertIsNone(record["disk"])

    def test_missing_data_is_unknown_not_zero(self):
        with tempfile.TemporaryDirectory() as work, patch("os.statvfs", side_effect=OSError()):
            self.assertEqual(SNAPSHOT(Path(work)), {"cpu": None, "memory": None, "disk": None, "uptime": None})


@unittest.skipUnless(shutil.which("quickshell"), "requires Quickshell")
class ObservationTests(unittest.TestCase):
    def test_styled_console_layout_on_tall_and_short_displays(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            shutil.copytree(ROOT / "qml", work / "qml")
            for name in ("Commons", "Ui"):
                (work / "qml" / name).symlink_to(Path("/usr/share/omarchy/shell") / name, target_is_directory=True)
            runpy.run_path(str(ROOT / "scripts/frame-style.py"))["apply_core_frames"](work / "qml", ROOT)
            raw = (work / "qml/prop/Prop.qml").read_text()

            def extract(marker):
                start = raw.index(marker)
                return raw[start:EXPRESSION_END(raw, raw.index("{", start))]

            frame = extract("Item {\n                id: frame")
            rows = extract("component TelemetryRow:") + "\n" + extract("component ConsoleAction:")
            colors = raw[raw.index("    readonly property color phosphor:"):raw.index("    Variants {")]
            for height in (960, 640):
                output_dir = Path(os.environ.get("AUSPEX_PREVIEW_DIR", str(work)))
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / f"auspex-{height}.png"
                qml = '''import QtQuick
import QtQuick.Window
import QtQuick.Controls as Controls
import "fx"
import "prop"
import "frames" as CogitatorFrames
Window {
  id: window
  width: 344; height: ''' + str(height) + '''; visible: true; color: "#030704"
  QtObject {
    id: mock
    property color phosphor: "#4fd06a"
    property color bright: "#7dff9a"
    property color pale: "#d2ffd9"
    property color dim: "#2f5b38"
    property color warn: "#e0ad2f"
    property color crit: "#ff5345"
    property color abyss: "#030704"
    property string propPosition: "right"
    property real propOpacity: 0.92
    property bool crtEnabled: false
    property bool animate: false
    property real ghosting: 0
    property real persistence: 0
    property bool screenBurn: false
    property bool cpuValid: true
    property bool memValid: true
    property bool diskValid: true
    property bool statsFresh: true
    property int cpuPercent: 26
    property string memText: "7.1 / 15.4 GiB"
    property string diskText: "44% USED / 230 GiB FREE"
    property bool cpuBusy: false
    property bool memoryBusy: false
    property bool diskBusy: false
    property string powerText: "064% DRAIN"
    property bool powerLow: false
    property bool powerCritical: false
    property string timeText: "12:34:56"
    property string dateText: "2026-10-29"
    property string channelText: "02"
    property string netText: "WIRELESS"
    property bool netOk: true
    property string voxText: "MUTED"
    property string relayText: "DORMANT"
    property bool streamPaused: false
    property string displayedRite: "LOGIC ENGINE / 26% UTILIZATION"
    property string currentRiteLevel: "normal"
    property bool typingRite: false
    property real crtIntensity: 0
    property string animationLevel: "minimal"
    property real flicker: 0
    property real noise: 0
    property bool brightnessFalloff: false
    property bool crtGlobal: false
    property string uptimeText: "2h 14m"
    property string sampleAgeText: "2s AGO"
    property var cpuHistory: [{time: 0, value: 10}, {time: 5000, value: 58}, {time: 10000, value: 26}]
    property var memoryHistory: [{time: 0, value: 43}, {time: 5000, value: 45}, {time: 10000, value: 46}]
    property var events: [
      {time: "12:34:56", message: "CHANNEL 02 / WORKSPACE SELECTED", level: "normal"},
      {time: "12:34:50", message: "POWER SOURCE / BATTERY", level: "normal"},
      {time: "12:34:30", message: "VOX ARRAY / MUTED", level: "normal"},
      {time: "12:34:15", message: "NOOSPHERIC LINK / WIRELESS", level: "normal"}]
    function inspectionHint(action) { return action; }
    function inspect(action) { }
  }
  Item {
    id: root
    anchors.fill: parent
    property var service: mock
''' + colors + frame + "\n" + rows + '''
    function inspectLayout() {
      return {viewport: viewport.height, content: stack.implicitHeight,
        instruments: instruments.implicitHeight, ledger: ledger.height,
        footer: footer.implicitHeight, width: frame.width};
    }
  }
  Timer {
    interval: 250; running: true
    onTriggered: {
      console.log("AUSPEX_LAYOUT " + JSON.stringify(root.inspectLayout()));
      window.contentItem.grabToImage(function(result) { result.saveToFile(''' + json.dumps(str(output_file)) + '''); Qt.quit(); });
    }
  }
}
'''
                file = work / "qml/shell.qml"
                file.write_text(qml)
                result = subprocess.run(["quickshell", "-p", str(file), "--no-color"],
                                        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software"),
                                        capture_output=True, text=True, timeout=15)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                self.assertNotIn("ReferenceError", output)
                self.assertNotIn("TypeError", output)
                self.assertNotIn("Binding loop", output)
                lines = [line.split("AUSPEX_LAYOUT ", 1)[1] for line in output.splitlines() if "AUSPEX_LAYOUT " in line]
                self.assertTrue(lines, output)
                geometry = json.loads(lines[-1])
                self.assertEqual(geometry["width"], 320)
                self.assertGreaterEqual(geometry["ledger"], 120)
                self.assertGreaterEqual(geometry["content"], geometry["viewport"])
                self.assertTrue(output_file.is_file(), output)

    def test_actual_service_functions_and_typing_timers(self):
        raw = (ROOT / "qml/Service.qml").read_text()

        def block(marker, opening=None):
            start = raw.index(marker)
            brace = raw.index("{", start)
            return raw[start:EXPRESSION_END(raw, brace)]

        methods = "\n".join(block("function " + name + "(") for name in (
            "loadSpirit", "reportEvent", "postEvent", "advanceRite", "nextRite", "updatePressure",
            "statsFailure", "parseStats", "inspect", "inspectionHint", "applyConfig"))
        methods += "\n" + block("function refreshPower(").replace("UPower.", "powerFixture.")
        hold_start = raw.rfind("Timer {", 0, raw.index("id: riteHold"))
        hold = raw[hold_start:EXPRESSION_END(raw, raw.index("{", hold_start))]
        char_start = raw.index("Timer {", hold_start + len(hold))
        char_timer = raw[char_start:EXPRESSION_END(raw, raw.index("{", char_start))]
        qml = '''import QtQuick
import Quickshell
import "''' + str(ROOT / "qml/prop/Auspex.js") + '''" as Auspex
import "''' + str(ROOT / "qml/prop/Spirit.js") + '''" as Spirit
ShellRoot {
  id: root
  property bool observing: true
  property bool propEnabled: true
  property bool textStreaming: true
  property string animationLevel: "full"
  readonly property bool animate: animationLevel !== "minimal"
  property int streamCharInterval: 20
  property bool streamPaused: false
  property var events: []
  property var pendingRites: []
  property var messageCatalog: null
  property var voiceCounters: ({})
  property var deferredEvents: []
  property double lastSpiritEventAt: 0
  property string currentRiteKind: "event"
  property var batteryObservation: null
  property string powerSource: ""
  property bool powerLow: false
  property bool powerCritical: false
  property bool netOk: true
  property string currentRite: ""
  property string displayedRite: ""
  property string currentRiteLevel: "normal"
  readonly property bool typingRite: textStreaming && animate && displayedRite.length < currentRite.length
  property int riteCursor: 0
  property bool cpuValid: false
  property bool memValid: false
  property bool diskValid: false
  property int cpuPercent: 0
  property int memPercent: 0
  property int diskPercent: 0
  property string memText: "--"
  property string diskText: "--"
  property real uptimeSeconds: 0
  property double lastStatsAt: 0
  property bool statsFresh: true
  property bool cpuBusy: false
  property bool memoryBusy: false
  property bool diskBusy: false
  property bool pollFailed: false
  property var previousCpu: null
  property var cpuHistory: []
  property var memoryHistory: []
  property string powerText: "FIXTURE POWER"
  property string netText: "FIXTURE NETWORK"
  property string held: ""
  QtObject { id: actionProc; property var command: []; property bool running: false }
  QtObject {
    id: powerFixture
    property bool onBattery: true
    property QtObject displayDevice: QtObject { property bool isPresent: true; property real percentage: 0.21 }
  }
  function verify(condition, message) { if (!condition) throw new Error(message); }
  function done(error) { console.log("AUSPEX_TEST " + JSON.stringify({error: error || "", events: events.length, pending: pendingRites.length})); Qt.quit(); }
  function sample(total, idle, memory) {
    root.parseStats(JSON.stringify({cpu: {total: total, idle: idle}, memory: {percent: memory, text: "4 / 10 GiB"}, disk: {percent: 30, freeGiB: 70}, uptime: 100}));
  }
''' + methods + "\n" + hold + "\n" + char_timer + "\n" + block("onStreamPausedChanged:") + '''
  onTextStreamingChanged: if (!textStreaming) displayedRite = currentRite
  onAnimateChanged: if (!animate) displayedRite = currentRite
  Component.onCompleted: {
    try {
      root.loadSpirit(''' + json.dumps((ROOT / "qml/prop/spirit-messages.json").read_text()) + ''');
      var valid = messageCatalog;
      root.loadSpirit("bad JSON");
      verify(messageCatalog === valid, "bad catalog edits keep the previous catalog");
      var invalid = JSON.parse(JSON.stringify(valid));
      invalid.events["battery.critical"].level = "normal";
      verify(!Spirit.validCatalog(invalid), "critical severity cannot be downgraded");
      delete invalid.events["cpu.high"];
      root.loadSpirit(JSON.stringify(invalid));
      verify(messageCatalog === valid, "incomplete catalogs keep the previous catalog");
      var waiting = [];
      for (var n = 0; n < 12; n++) waiting = Spirit.enqueue(waiting, {id: "normal-" + n, level: "normal"});
      waiting = Spirit.enqueue(waiting, {id: "urgent", level: "critical"});
      verify(waiting.length === 8 && waiting[0].id === "urgent" && waiting[7].id === "normal-11", "priority queue is bounded and keeps latest normal events");
      var step = Spirit.batteryStep(null, 82, true);
      verify(step.event === "", "battery startup is not a milestone");
      step = Spirit.batteryStep(step.state, 80, true);
      verify(step.event === "battery.drain" && step.boundary === 80, "discharge reaches a tenth");
      step = Spirit.batteryStep(step.state, 79, true);
      verify(step.event === "", "no per-percent battery chatter");
      step = Spirit.batteryStep(step.state, 81, true);
      step = Spirit.batteryStep(step.state, 80, true);
      verify(step.event === "", "battery threshold jitter is not repeated");
      step = Spirit.batteryStep(null, 79, false);
      step = Spirit.batteryStep(step.state, 80, false);
      verify(step.event === "battery.charge", "charging reaches a tenth");
      step = Spirit.batteryStep(null, 83, true);
      step = Spirit.batteryStep(step.state, 67, true);
      verify(step.boundary === 70 && step.state.percent === 67, "large drop reports latest crossed boundary with actual percent");
      step = Spirit.batteryStep(step.state, 67, false);
      verify(step.event === "", "power-source changes rebaseline milestones");
      verify(Spirit.batteryStep(null, null, true).event === "", "missing battery is not zero");
      verify(Auspex.cpuUsage(null, {total: 100, idle: 90}) === null, "first CPU sample must be unknown");
      verify(Auspex.cpuUsage({total: 100, idle: 90}, {total: 90, idle: 80}) === null, "counter reset must be unknown");
      verify(Auspex.appendSample([], null, 0).length === 0, "no fabricated history");
      verify(Auspex.appendSample([{time: 0, value: 30}], 40, 130000).length === 1, "history is time-bounded");
      sample(1000, 900, 40);
      verify(!cpuValid && cpuHistory.length === 0, "first sample does not manufacture CPU");
      sample(1100, 980, 43);
      verify(cpuPercent === 20 && cpuHistory.length === 1, "CPU delta usage");
      sample(1200, 980, 43);
      verify(cpuBusy && events[0].level === "warning", "real high CPU event");
      verify(events[0].message.indexOf("100%") !== -1 && currentRite.indexOf("LABOUR") !== -1,
        "factual event log and spirited commentary stay separate");
      root.applyConfig({streamCharInterval: 500});
      verify(streamCharInterval === 200, "typing upper bound");
      root.applyConfig({streamCharInterval: 20});
      root.inspect("network");
      verify(actionProc.command.join(" ") === "omarchy-shell shell summon omarchy.network {}", "native network controls");
      verify(Auspex.actionCommand("processes").join(" ") === "omarchy-launch-or-focus-tui btop", "process action");
      verify(Auspex.actionCommand("arbitrary-command").length === 0, "actions are allowlisted");
      typingCheck.start();
    } catch (e) { done(String(e)); }
  }
  Timer {
    id: typingCheck; interval: 160
    onTriggered: {
      try {
        verify(displayedRite.length > 0 && displayedRite.length < currentRite.length, "character-by-character stream");
        root.streamPaused = true;
        root.held = displayedRite;
        pauseCheck.start();
      } catch (e) { done(String(e)); }
    }
  }
  Timer {
    id: pauseCheck; interval: 120
    onTriggered: {
      try {
        verify(displayedRite === held, "hold freezes text");
        root.streamPaused = false;
        root.textStreaming = false;
        verify(displayedRite === currentRite, "streaming off reveals whole message");
        sample(1300, 1060, 43);
        verify(!cpuBusy && events[0].message.indexOf("SUBSIDED") !== -1, "load hysteresis recovery");
        var count = events.length;
        root.parseStats("bad json"); root.parseStats("bad json");
        verify(events.length === count + 1, "failed samples are not spammed");
        for (var i = 0; i < 45; i++) root.postEvent("FIXTURE EVENT " + i, "normal");
        verify(events.length === 32 && pendingRites.length === 8, "ledger and queue bounded");
        root.textStreaming = true;
        root.animationLevel = "minimal";
        root.advanceRite();
        verify(displayedRite === currentRite, "reduced motion has no typing");
        var recent = currentRite;
        root.nextRite();
        verify(currentRite === recent, "idle liturgy does not displace pending events");
        sample(1400, 1140, 43);
        verify(!pollFailed && events[0].id === "telemetry.restored", "sampling recovery is observed");
        root.pendingRites = [];
        riteHold.stop();
        root.lastSpiritEventAt = Date.now() - 60000;
        root.cpuPercent = 5;
        var beforeIdle = events.length;
        root.nextRite();
        verify(currentRiteKind === "idle" && events.length === beforeIdle,
          "quiet classics do not fabricate observation log records");
        root.refreshPower();
        powerFixture.displayDevice.percentage = 0.20;
        root.refreshPower();
        verify(events[0].id === "battery.low", "low battery supersedes milestone chatter");
        powerFixture.displayDevice.percentage = 0.10;
        root.refreshPower();
        verify(currentRiteLevel === "critical" && currentRite.indexOf("10%") !== -1,
          "critical battery interrupts idle/normal commentary");
        root.reportEvent("audio.active");
        verify(pendingRites[pendingRites.length - 1].voice === "VOX ARRAY / OUTPUT ACTIVE",
          "no whimsical normal messages during critical battery");
        var quiet = currentRite;
        riteHold.stop(); root.pendingRites = [];
        root.lastSpiritEventAt = Date.now() - 60000;
        root.nextRite();
        verify(currentRite === quiet, "no idle whimsy while a power warning is active");
        done("");
      } catch (e) { done(String(e)); }
    }
  }
}
'''
        with tempfile.TemporaryDirectory() as work:
            file = Path(work) / "shell.qml"
            file.write_text(qml)
            result = subprocess.run(["quickshell", "-p", str(file), "--no-color"],
                                    env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
                                    capture_output=True, text=True, timeout=15)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            lines = [line.split("AUSPEX_TEST ", 1)[1] for line in output.splitlines() if "AUSPEX_TEST " in line]
            self.assertTrue(lines, output)
            self.assertEqual(json.loads(lines[-1])["error"], "", output)


if __name__ == "__main__":
    unittest.main()
