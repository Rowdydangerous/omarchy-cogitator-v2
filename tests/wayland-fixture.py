"""Isolated software-rendered Wayland server for real Quickshell window tests."""
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import tempfile
import time


@contextmanager
def headless_wayland(width=1000, height=500):
    base = "/tmp/opencode" if Path("/tmp/opencode").is_dir() else None
    with tempfile.TemporaryDirectory(prefix="wl-", dir=base) as work:
        work = Path(work)
        runtime = work / "run"
        runtime.mkdir(mode=0o700)
        config = work / "sway.conf"
        config.write_text(f"xwayland disable\noutput HEADLESS-1 mode {width}x{height}\n")
        env = dict(os.environ, XDG_RUNTIME_DIR=str(runtime), WLR_BACKENDS="headless",
                   WLR_RENDERER="pixman", WLR_HEADLESS_OUTPUTS="1",
                   WLR_LIBINPUT_NO_DEVICES="1", QT_QPA_PLATFORM="wayland",
                   QT_QUICK_BACKEND="software")
        for key in ("WAYLAND_DISPLAY", "DISPLAY", "SWAYSOCK", "HYPRLAND_INSTANCE_SIGNATURE",
                    "DBUS_SESSION_BUS_ADDRESS"):
            env.pop(key, None)
        with (work / "sway.log").open("w+") as log:
            server = subprocess.Popen(["sway", "--config", str(config)], env=env,
                                      stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    sockets = [p for p in runtime.glob("wayland-*") if p.is_socket()]
                    ipc = list(runtime.glob("sway-ipc.*.sock"))
                    if sockets and ipc:
                        env["WAYLAND_DISPLAY"] = sockets[0].name
                        env["SWAYSOCK"] = str(ipc[0])
                        break
                    if server.poll() is not None:
                        break
                    time.sleep(0.02)
                else:
                    raise RuntimeError("Headless Wayland server did not become ready")
                if "WAYLAND_DISPLAY" not in env:
                    log.seek(0)
                    raise RuntimeError("Headless Wayland startup failed:\n" + log.read())
                yield env
            finally:
                if server.poll() is None:
                    server.terminate()
                    try:
                        server.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait()
