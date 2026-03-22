#!/usr/bin/env python3
"""
Focus Flow: Micro-task launcher for Claude Code thinking time.

Launched by hook_runner.py when UserPromptSubmit fires. Waits for
min_thinking_seconds, then starts a micro-task if Claude is still
processing. Automatically killed by hook_runner.py when Stop fires.

Usage (called by hook_runner.py, not directly):
    python focus-flow.py <mode> <delay> <marker_path> <url> <command> [breathing_pattern]
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
TASKS_DIR = SCRIPT_DIR / "focus-flow-tasks"


# =============================================================================
# BREATHING EXERCISE
# =============================================================================

def _load_breathing_pattern(pattern_name: str) -> dict:
    """Load a breathing pattern from the JSON data file."""
    patterns_file = TASKS_DIR / "breathing_patterns.json"
    try:
        data = json.loads(patterns_file.read_text(encoding="utf-8"))
        patterns = data.get("patterns", {})
        return patterns.get(pattern_name, patterns.get("4-7-8", {}))
    except (json.JSONDecodeError, OSError):
        # Fallback 4-7-8 pattern
        return {
            "name": "4-7-8 Relaxing Breath",
            "steps": [
                {"action": "Inhale", "emoji": "\U0001f32c\ufe0f", "seconds": 4},
                {"action": "Hold", "emoji": "\u23f8\ufe0f", "seconds": 7},
                {"action": "Exhale", "emoji": "\U0001f4a8", "seconds": 8},
            ],
            "cycles": 3,
        }


def _breathing_script_content(pattern_name: str) -> str:
    """Generate the Python script content for the breathing exercise terminal."""
    pattern = _load_breathing_pattern(pattern_name)
    name = pattern.get("name", "Breathing Exercise")
    steps = pattern.get("steps", [])
    cycles = pattern.get("cycles", 3)

    # Build a self-contained Python script as a string
    return f'''#!/usr/bin/env python3
import sys, time

name = {repr(name)}
steps = {repr(steps)}
cycles = {cycles}

CLEAR = "\\033[2J\\033[H"
BOLD = "\\033[1m"
DIM = "\\033[2m"
CYAN = "\\033[36m"
GREEN = "\\033[32m"
YELLOW = "\\033[33m"
RESET = "\\033[0m"

def progress_bar(current, total, width=30):
    filled = int(width * current / total)
    bar = "\u2588" * filled + "\u2591" * (width - filled)
    return bar

print(CLEAR, end="")
print(f"{{BOLD}}{{CYAN}}")
print("  \u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e")
print("  \u2502  Focus Flow \u2014 Breathing Exercise    \u2502")
print(f"  \u2502  {{name:<37s}}\u2502")
print("  \u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f")
print(f"{{RESET}}")
print(f"  {{DIM}}Claude is thinking... stay present.{{RESET}}")
print(f"  {{DIM}}This window closes automatically when Claude finishes.{{RESET}}")
print()

try:
    for cycle in range(1, cycles + 1):
        print(f"  {{BOLD}}Cycle {{cycle}}/{{cycles}}{{RESET}}")
        for step in steps:
            action = step["action"]
            emoji = step.get("emoji", "")
            secs = step["seconds"]
            color = GREEN if "Inhale" in action else YELLOW if "Hold" in action else CYAN
            for s in range(secs, 0, -1):
                bar = progress_bar(secs - s, secs)
                print(f"\\r  {{color}}{{emoji}} {{action:<8s}} {{bar}} {{s:>2d}}s {{RESET}}", end="", flush=True)
                time.sleep(1)
            print(f"\\r  {{color}}{{emoji}} {{action:<8s}} {{progress_bar(secs, secs)}}  \u2713 {{RESET}}")
        print()

    print(f"  {{GREEN}}{{BOLD}}\u2728 Great job! Stay focused. \u2728{{RESET}}")
    print(f"  {{DIM}}Waiting for Claude to finish...{{RESET}}")

    # Keep window open until killed by stop_focus_flow
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    pass
'''


def run_breathing(pattern_name: str = "4-7-8", pid_file: Path = None) -> None:
    """Launch a breathing exercise in a new terminal window."""
    script_content = _breathing_script_content(pattern_name)
    tmp_script = Path(os.environ.get("TEMP", "/tmp")) / "claude_focus_breathing.py"
    tmp_script.write_text(script_content, encoding="utf-8")

    system = platform.system()
    python_cmd = sys.executable

    try:
        if system == "Windows":
            proc = subprocess.Popen(
                ["cmd", "/c", "start", "Focus Flow - Breathing",
                 python_cmd, str(tmp_script)],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        elif system == "Darwin":
            # macOS: use osascript to open Terminal
            proc = subprocess.Popen([
                "osascript", "-e",
                f'tell application "Terminal" to do script "{python_cmd} {tmp_script}"'
            ])
        else:
            # Linux: try common terminal emulators
            for term_cmd in ["xterm", "gnome-terminal", "konsole", "xfce4-terminal"]:
                if shutil.which(term_cmd):
                    if term_cmd == "xterm":
                        proc = subprocess.Popen([
                            term_cmd, "-title", "Focus Flow - Breathing",
                            "-e", python_cmd, str(tmp_script)
                        ])
                    elif term_cmd == "gnome-terminal":
                        proc = subprocess.Popen([
                            term_cmd, "--title=Focus Flow - Breathing",
                            "--", python_cmd, str(tmp_script)
                        ])
                    else:
                        proc = subprocess.Popen([
                            term_cmd, "-e", f"{python_cmd} {tmp_script}"
                        ])
                    break
            else:
                # Fallback: run inline (no separate window)
                proc = subprocess.Popen([python_cmd, str(tmp_script)])

        # Write the terminal process PID for cleanup
        if pid_file and proc:
            pid_file.write_text(str(proc.pid), encoding="utf-8")

    except Exception:
        pass


# =============================================================================
# HYDRATION REMINDER
# =============================================================================

def run_hydration(pid_file: Path = None) -> None:
    """Send a hydration/stretch reminder via desktop notification."""
    messages = [
        ("Hydration Check", "Time to drink some water! Stay hydrated while Claude thinks."),
        ("Stretch Break", "Stand up and stretch! Roll your shoulders. Claude is still working."),
        ("Eye Rest", "Look away from the screen for 20 seconds. Follow the 20-20-20 rule."),
        ("Posture Check", "Sit up straight! Check your posture while Claude processes."),
        ("Deep Breath", "Take 3 deep breaths right now. In through nose, out through mouth."),
    ]

    import random
    title, message = random.choice(messages)

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen([
                "osascript", "-e",
                f'display notification "{message}" with title "Focus Flow - {title}"'
            ])
        elif system == "Windows":
            ps_cmd = (
                '[void][System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); '
                '$n = New-Object System.Windows.Forms.NotifyIcon; '
                '$n.Icon = [System.Drawing.SystemIcons]::Information; '
                '$n.Visible = $true; '
                f'$n.ShowBalloonTip(10000, "Focus Flow - {title}", "{message}", '
                '[System.Windows.Forms.ToolTipIcon]::Info); '
                'Start-Sleep -Seconds 11; $n.Dispose()'
            )
            proc = subprocess.Popen(
                ["powershell.exe", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            if pid_file and proc:
                pid_file.write_text(str(proc.pid), encoding="utf-8")
        else:
            # Linux / WSL
            if shutil.which("notify-send"):
                subprocess.Popen([
                    "notify-send", f"Focus Flow - {title}", message,
                    "-i", "dialog-information", "-t", "15000"
                ])
            elif shutil.which("powershell.exe"):
                # WSL fallback
                ps_cmd = (
                    '[void][System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); '
                    '$n = New-Object System.Windows.Forms.NotifyIcon; '
                    '$n.Icon = [System.Drawing.SystemIcons]::Information; '
                    '$n.Visible = $true; '
                    f'$n.ShowBalloonTip(10000, "Focus Flow - {title}", "{message}", '
                    '[System.Windows.Forms.ToolTipIcon]::Info); '
                    'Start-Sleep -Seconds 11; $n.Dispose()'
                )
                subprocess.Popen(["powershell.exe", "-WindowStyle", "Hidden", "-Command", ps_cmd])
    except Exception:
        pass


# =============================================================================
# URL & COMMAND MODES
# =============================================================================

def run_url(url: str) -> None:
    """Open a URL in the default browser."""
    if url:
        webbrowser.open(url)


def run_command(cmd: str, pid_file: Path = None) -> None:
    """Run a custom shell command."""
    if cmd:
        try:
            proc = subprocess.Popen(cmd, shell=True)
            if pid_file and proc:
                pid_file.write_text(str(proc.pid), encoding="utf-8")
        except Exception:
            pass


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main() -> int:
    if len(sys.argv) < 6:
        print("Usage: focus-flow.py <mode> <delay> <marker_path> <url> <command> [breathing_pattern]", file=sys.stderr)
        return 1

    mode = sys.argv[1]
    delay = float(sys.argv[2])
    marker = Path(sys.argv[3])
    url = sys.argv[4]
    command = sys.argv[5]
    breathing_pattern = sys.argv[6] if len(sys.argv) > 6 else "4-7-8"

    pid_file = marker.parent / "focus_flow_pid"

    # Wait for minimum thinking time
    time.sleep(delay)

    # Check if Claude already finished (marker removed by stop_focus_flow)
    if not marker.exists():
        return 0  # Claude finished quickly, no micro-task needed

    # Launch the micro-task
    if mode == "breathing":
        run_breathing(breathing_pattern, pid_file)
    elif mode == "hydration":
        run_hydration(pid_file)
    elif mode == "url":
        run_url(url)
    elif mode == "command":
        run_command(command, pid_file)
    else:
        run_hydration(pid_file)  # fallback

    return 0


if __name__ == "__main__":
    sys.exit(main())
