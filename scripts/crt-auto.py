#!/usr/bin/env python3
"""Suspend the compositor CRT shader while a video is fullscreen.

Watches Hyprland's event socket, and when the active window is fullscreen and
belongs to a video player or browser (CRT_AUTO_VIDEO_CLASSES), clears
decoration:screen_shader with a live hl.config() call. Restores the previous
shader when the fullscreen window goes away.

This is deliberately runtime-only: it never edits looknfeel.lua or the
Cogitator config, so the user's CRT_GLOBAL preference is untouched.
"""
from __future__ import annotations

import glob
import json
import os
import select
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
CONF = CONFIG_HOME / "cogitator-v2/cogitator.conf"
FRAG = CONFIG_HOME / "cogitator-v2/crt.frag"
RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))

# Classes that count as video when fullscreen. Override with
# CRT_AUTO_VIDEO_CLASSES in cogitator.conf; "*" means any fullscreen window.
DEFAULT_CLASSES = [
    "mpv", "vlc", "celluloid", "haruna", "totem", "smplayer", "kodi",
    "plex", "jellyfin", "stremio", "freetube",
    "firefox", "chromium", "google-chrome", "chrome", "brave",
    "brave-browser", "microsoft-edge", "opera", "vivaldi", "vivaldi-stable",
    "zen", "zen-browser", "librewolf", "floorp", "waterfox", "qutebrowser",
    "epiphany",
]
RELEVANT_EVENTS = {
    "fullscreen", "activewindow", "openwindow", "closewindow",
    "workspace", "focusedmon", "movewindow",
}


def log(message: str) -> None:
    print(f"crt-auto: {message}", flush=True)


def read_conf() -> str:
    try:
        return CONF.read_text()
    except OSError:
        return ""


def conf_value(raw: str, key: str, default: str = "") -> str:
    for line in raw.splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        name, value = line.split("=", 1)
        if name.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        return value
    return default


def conf_bool(raw: str, key: str, default: bool = False) -> bool:
    return conf_value(raw, key, "true" if default else "false").lower() in (
        "1", "true", "yes", "on",
    )


def find_socket() -> str:
    signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    if signature:
        candidate = RUNTIME / "hypr" / signature / ".socket2.sock"
        if candidate.exists():
            return str(candidate)
    candidates = glob.glob(str(RUNTIME / "hypr" / "*" / ".socket2.sock"))
    if not candidates:
        return ""
    return max(candidates, key=os.path.getmtime)


def hyprctl_json(*args: str) -> dict:
    try:
        result = subprocess.run(
            ["hyprctl", "-j", *args],
            capture_output=True, text=True, timeout=3,
        )
        return json.loads(result.stdout or "{}")
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {}


def current_shader() -> str:
    try:
        result = subprocess.run(
            ["hyprctl", "getoption", "decoration:screen_shader"],
            capture_output=True, text=True, timeout=3,
        )
        for line in result.stdout.splitlines():
            if line.startswith("str:"):
                return line[4:].strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def set_shader(path: str) -> None:
    # hyprctl keyword is rejected by the Lua parser; hl.config via eval works.
    code = 'hl.config({ decoration = { screen_shader = %s } })' % json.dumps(path or "")
    try:
        subprocess.run(
            ["hyprctl", "eval", code],
            capture_output=True, text=True, timeout=3,
        )
    except (OSError, subprocess.SubprocessError) as error:
        log(f"eval failed: {error}")


def is_fullscreen_video(classes: list[str]) -> bool:
    window = hyprctl_json("activewindow")
    if not window:
        return False
    try:
        if int(window.get("fullscreen", 0) or 0) < 2:
            return False
    except (TypeError, ValueError):
        return False
    if classes == ["*"]:
        return True
    names = {
        str(window.get("class") or "").lower(),
        str(window.get("initialClass") or "").lower(),
    }
    return bool(names & set(classes))


def main() -> None:
    suspended = False
    saved_shader = ""

    def restore() -> None:
        nonlocal suspended, saved_shader
        if not suspended:
            return
        target = saved_shader or (str(FRAG) if FRAG.exists() else "")
        set_shader(target)
        log(f"restored shader {target or '(none)'}")
        suspended = False
        saved_shader = ""

    def check() -> None:
        nonlocal suspended, saved_shader
        raw = read_conf()
        if not conf_bool(raw, "CRT_AUTO_VIDEO", False):
            restore()
            return
        if not conf_bool(raw, "CRT_GLOBAL", True):
            # Global CRT is off; there is nothing to suspend. Drop any saved
            # value so a later enable starts clean.
            suspended = False
            saved_shader = ""
            return
        configured = conf_value(raw, "CRT_AUTO_VIDEO_CLASSES", "")
        classes = [item.strip().lower() for item in configured.split(",") if item.strip()]
        classes = classes or [item.lower() for item in DEFAULT_CLASSES]
        wanted = is_fullscreen_video(classes)
        if wanted and not suspended:
            shader = current_shader()
            if shader:
                saved_shader = shader
                set_shader("")
                suspended = True
                log("suspended shader for fullscreen video")
        elif not wanted and suspended:
            restore()

    def stop(*_args) -> None:
        restore()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    check()
    while True:
        path = find_socket()
        if not path:
            time.sleep(2)
            continue
        try:
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            connection.connect(path)
            connection.setblocking(False)
        except OSError as error:
            log(f"connect failed: {error}")
            time.sleep(2)
            continue
        log(f"watching {path}")
        buffer = b""
        pending = False
        deadline = 0.0
        try:
            while True:
                ready, _, _ = select.select([connection], [], [], 0.25)
                if ready:
                    data = connection.recv(65536)
                    if not data:
                        raise ConnectionError("event socket closed")
                    buffer += data
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        event = line.split(b">>", 1)[0].decode("utf-8", "replace")
                        if event in RELEVANT_EVENTS:
                            pending = True
                            deadline = time.monotonic() + 0.15
                if pending and time.monotonic() >= deadline:
                    pending = False
                    check()
        except (OSError, ConnectionError) as error:
            log(f"event loop: {error}")
        finally:
            try:
                connection.close()
            except OSError:
                pass
        # Re-check after reconnecting: a fullscreen video may still be up.
        time.sleep(1)
        check()


if __name__ == "__main__":
    main()
