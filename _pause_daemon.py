#!/usr/bin/env python3
"""
Pause daemon - monitors X11 focus to SIGSTOP/SIGCONT wallpaper processes.
Runs as a separate process, no dependency on tkinter or the GUI.
"""
import subprocess
import signal
import sys
import os
import time

WPE_NAME = "linux-wallpaperengine"
MPV_NAME = "mpv"
CHECK_INTERVAL = 0.5


def get_wallpaper_pids():
    pids = set()
    try:
        for name in [WPE_NAME, MPV_NAME]:
            r = subprocess.run(["pgrep", "-f", name], capture_output=True, text=True, timeout=2)
            for pid in r.stdout.strip().split():
                if pid.isdigit():
                    pids.add(int(pid))
    except Exception:
        pass
    return pids


def is_x11_focused():
    try:
        r = subprocess.run(
            ["xdotool", "getwindowfocus"],
            capture_output=True, text=True, timeout=1
        )
        return bool(r.stdout.strip())
    except Exception:
        return True


def main():
    paused = False

    def cleanup(signum, frame):
        nonlocal paused
        if paused:
            for pid in get_wallpaper_pids():
                try:
                    os.kill(pid, signal.SIGCONT)
                except (ProcessLookupError, OSError):
                    pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    while True:
        pids = get_wallpaper_pids()
        if pids:
            focused = is_x11_focused()
            if focused and paused:
                for pid in pids:
                    try:
                        os.kill(pid, signal.SIGCONT)
                    except (ProcessLookupError, OSError):
                        pass
                paused = False
            elif not focused and not paused:
                for pid in pids:
                    try:
                        os.kill(pid, signal.SIGSTOP)
                    except (ProcessLookupError, OSError):
                        pass
                paused = True
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
