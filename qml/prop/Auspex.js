// Pure readout helpers. No hardware control or fabricated samples.
function cpuUsage(previous, current) {
    if (!previous || !current) return null;
    var elapsed = current.total - previous.total;
    var idle = current.idle - previous.idle;
    if (elapsed <= 0 || idle < 0 || idle > elapsed) return null;
    return Math.max(0, Math.min(100, Math.round(100 * (elapsed - idle) / elapsed)));
}

function appendSample(history, value, now) {
    if (value === null || !isFinite(value)) return history;
    return history.filter(function(point) { return now - point.time < 120000; })
        .concat([{time: now, value: value}]).slice(-24);
}

function duration(seconds) {
    var minutes = Math.floor(Math.max(0, seconds) / 60);
    var hours = Math.floor(minutes / 60);
    return hours > 0 ? hours + "h " + (minutes % 60) + "m" : minutes + "m";
}

function actionCommand(action) {
    // Quickshell captures a Process's stdout/stderr with pipes. Launchers that
    // detach (setsid, xdg-open, GUI forks) outlive the short-lived parent, and
    // Quickshell closes the pipes as soon as that parent exits — the detached
    // child then dies on SIGPIPE before it can map a window. Redirect stdio and
    // detach so no descendant keeps the pipe open, and so the Process can exit
    // promptly instead of blocking the next console action.
    if (action === "processes") return ["bash", "-c", "exec omarchy-launch-or-focus-tui btop >/dev/null 2>&1"];
    if (action === "files") return ["bash", "-c", "setsid -f xdg-open \"$HOME\" </dev/null >/dev/null 2>&1"];
    if (action === "control") return ["omarchy-shell", "cogitator.control", "open"];
    if (action === "channels") return ["omarchy-shell", "cogitator.control", "page", "Surfaces"];
    var targets = {network: "omarchy.network", audio: "omarchy.audio", power: "omarchy.power",
                   bluetooth: "omarchy.bluetooth", clock: "omarchy.clock"};
    return targets[action] ? ["omarchy-shell", "shell", "summon", targets[action], "{}"] : [];
}

function actionHint(action) {
    var hints = {processes: "Open or focus the process monitor", files: "Open Files",
                 control: "Open Control Sanctum", channels: "Open console and workspace settings",
                 network: "Open network controls", audio: "Open audio controls",
                 power: "Open power controls", bluetooth: "Open Bluetooth controls", clock: "Open calendar"};
    return hints[action] || "";
}
