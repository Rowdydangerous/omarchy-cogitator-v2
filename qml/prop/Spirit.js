// Pure policy/formatting helpers. Wording belongs in spirit-messages.json.
var levels = {normal: 0, warning: 1, critical: 2};
var pressureLimits = {cpu: [90, 75], memory: [90, 85], disk: [90, 85]};
var eventIds = ["session.open", "workspace.selected", "network.up", "network.down",
    "relay.quiet", "relay.changed", "audio.muted", "audio.active", "audio.missing",
    "power.external", "power.battery", "battery.drain", "battery.charge", "battery.low",
    "battery.critical", "battery.recovered", "cpu.high", "cpu.clear", "memory.high",
    "memory.clear", "disk.high", "disk.clear", "telemetry.stale", "telemetry.failed",
    "telemetry.restored", "inspection.failed", "inspection.unavailable"];

function validCatalog(catalog) {
    if (!catalog || catalog.version !== 1 || !Array.isArray(catalog.idle) || !catalog.idle.length
        || !catalog.events || typeof catalog.events !== "object") return false;
    if (!catalog.idle.every(function(line) { return typeof line === "string" && line.length > 0; })) return false;
    return Object.keys(catalog.events).every(function(id) {
        var event = catalog.events[id];
        return event && levels[event.level] !== undefined && typeof event.log === "string" && event.log.length > 0
            && Array.isArray(event.voice) && event.voice.length > 0
            && event.voice.every(function(line) { return typeof line === "string" && line.length > 0; });
    }) && eventIds.every(function(id) { return !!catalog.events[id]; })
       && catalog.events["battery.critical"].level === "critical";
}

function format(template, values) {
    return template.replace(/\{([a-zA-Z]+)\}/g, function(match, key) {
        return values[key] === undefined || values[key] === null ? "--" : String(values[key]);
    });
}

function message(catalog, id, values, index) {
    var definition = catalog.events[id];
    if (!definition) return null;
    return {id: id, level: definition.level, message: format(definition.log, values),
            voice: format(definition.voice[index % definition.voice.length], values)};
}

function enqueue(queue, entry) {
    // Keep the latest value of a queued event type; urgent events go first.
    var result = queue.filter(function(old) { return !entry.id || old.id !== entry.id; });
    var index = 0;
    while (index < result.length && levels[result[index].level] >= levels[entry.level]) index++;
    result.splice(index, 0, entry);
    if (result.length > 8) {
        var lowest = levels[result[result.length - 1].level];
        var oldest = 0;
        while (levels[result[oldest].level] > lowest) oldest++;
        result.splice(oldest, 1);
    }
    return result;
}

function pressure(active, metric, value) {
    var limit = pressureLimits[metric];
    if (!limit || !isFinite(value)) return {active: active, event: ""};
    if (!active && value >= limit[0]) return {active: true, event: metric + ".high"};
    if (active && value <= limit[1]) return {active: false, event: metric + ".clear"};
    return {active: active, event: ""};
}

function batteryStep(previous, percent, discharging) {
    if (percent === null || !isFinite(percent) || percent < 0 || percent > 100)
        return {state: null, event: ""};
    var state = {percent: percent, discharging: discharging, lastNotice: previous ? previous.lastNotice : ""};
    if (!previous || previous.discharging !== discharging) {
        state.lastNotice = "";
        return {state: state, event: ""};
    }
    var before = discharging ? Math.ceil(previous.percent / 10) : Math.floor(previous.percent / 10);
    var after = discharging ? Math.ceil(percent / 10) : Math.floor(percent / 10);
    var crossed = discharging ? after < before : after > before;
    var key = (discharging ? "drain:" : "charge:") + after;
    if (!crossed || key === state.lastNotice) return {state: state, event: ""};
    state.lastNotice = key;
    return {state: state, event: discharging ? "battery.drain" : "battery.charge", boundary: after * 10};
}

function canIdle(state, now) {
    return state.fresh && state.cpuValid && state.cpu < 30 && !state.warning
        && !state.pending && !state.typing && !state.paused && now - state.lastEvent >= 30000;
}
