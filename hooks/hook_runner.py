#!/usr/bin/env python3
"""
Claude Code Audio Hooks - Python Hook Runner
Cross-platform hook runner that works on Windows, macOS, and Linux.
This replaces the bash-based hooks for better Windows compatibility.

Usage:
    python hook_runner.py <hook_type>

Hook types: notification, stop, pretooluse, posttooluse, posttoolusefailure,
            userpromptsubmit, subagent_stop, subagent_start, precompact,
            session_start, session_end, permission_request,
            teammate_idle, task_completed

Environment Variables:
    CLAUDE_HOOKS_DEBUG=1    Enable debug logging
"""

import json
import os
import shutil
import sys
import time
import subprocess
import platform
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

# =============================================================================
# DEBUG LOGGING SYSTEM
# =============================================================================

DEBUG = os.environ.get("CLAUDE_HOOKS_DEBUG", "").lower() in ("1", "true", "yes")

def get_log_dir() -> Path:
    """Get the log directory, creating it if necessary."""
    if platform.system() == "Windows":
        base = Path(os.environ.get("TEMP", os.environ.get("TMP", "C:/Windows/Temp")))
    else:
        base = Path("/tmp")
    log_dir = base / "claude_audio_hooks_queue" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def log_debug(message: str) -> None:
    """Log debug message if debug mode is enabled."""
    if not DEBUG:
        return
    try:
        log_file = get_log_dir() / "debug.log"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} | DEBUG | {message}\n")
        # Keep only last 500 entries
        lines = log_file.read_text(encoding="utf-8").splitlines()
        if len(lines) > 500:
            log_file.write_text("\n".join(lines[-500:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def log_error(message: str) -> None:
    """Log error message (always logged)."""
    try:
        log_file = get_log_dir() / "errors.log"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} | ERROR | {message}\n")
        # Keep only last 200 entries
        lines = log_file.read_text(encoding="utf-8").splitlines()
        if len(lines) > 200:
            log_file.write_text("\n".join(lines[-200:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def log_trigger(hook_type: str, status: str, details: str = "") -> None:
    """Log hook trigger with status."""
    try:
        log_file = get_log_dir() / "hook_triggers.log"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"{timestamp} | {hook_type} | {status}"
        if details:
            line += f" | {details}"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        # Keep only last 200 entries
        lines = log_file.read_text(encoding="utf-8").splitlines()
        if len(lines) > 200:
            log_file.write_text("\n".join(lines[-200:]) + "\n", encoding="utf-8")
    except Exception:
        pass

# =============================================================================
# PATH UTILITIES
# =============================================================================

def normalize_path(path_str: str) -> str:
    """Convert various path formats to the platform's native format.

    Handles:
    - Git Bash/MSYS2: /c/Users/... -> C:/Users/...
    - WSL2: /mnt/c/Users/... -> C:/Users/...
    - Cygwin: /cygdrive/c/... -> C:/...
    """
    if platform.system() != "Windows":
        return path_str

    path_str = path_str.strip()

    log_debug(f"normalize_path input: {path_str}")

    # Handle WSL2 style paths: /mnt/c/... -> C:/...
    if path_str.startswith("/mnt/") and len(path_str) >= 6:
        drive_letter = path_str[5].upper()
        if drive_letter.isalpha():
            rest = path_str[6:] if len(path_str) > 6 else "/"
            result = f"{drive_letter}:{rest}"
            log_debug(f"normalize_path WSL2: {path_str} -> {result}")
            return result

    # Handle Cygwin style paths: /cygdrive/c/... -> C:/...
    if path_str.startswith("/cygdrive/") and len(path_str) >= 11:
        drive_letter = path_str[10].upper()
        if drive_letter.isalpha():
            rest = path_str[11:] if len(path_str) > 11 else "/"
            result = f"{drive_letter}:{rest}"
            log_debug(f"normalize_path Cygwin: {path_str} -> {result}")
            return result

    # Handle Git Bash/MSYS2 style paths: /d/... -> D:/...
    if len(path_str) >= 2 and path_str[0] == '/' and path_str[1].isalpha():
        drive_letter = path_str[1].upper()
        if len(path_str) == 2:
            result = f"{drive_letter}:/"
        elif path_str[2] == '/':
            result = f"{drive_letter}:{path_str[2:]}"
        else:
            # Not a drive path, return as-is
            return path_str
        log_debug(f"normalize_path Git Bash: {path_str} -> {result}")
        return result

    return path_str


def escape_powershell_string(s: str) -> str:
    """Escape a string for safe use in PowerShell double-quoted strings."""
    # Escape backticks, double quotes, and dollar signs
    s = s.replace('`', '``')
    s = s.replace('"', '`"')
    s = s.replace('$', '`$')
    return s


def get_safe_temp_dir() -> Path:
    """Get a safe temporary directory that exists and is writable."""
    candidates: List[Path] = []

    if platform.system() == "Windows":
        # Windows: prefer TEMP, then TMP, then USERPROFILE/Temp, then fallback
        for env_var in ["TEMP", "TMP"]:
            val = os.environ.get(env_var)
            if val:
                candidates.append(Path(val))

        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            candidates.append(Path(userprofile) / "AppData" / "Local" / "Temp")

        # Windows fallback
        windir = os.environ.get("WINDIR", "C:/Windows")
        candidates.append(Path(windir) / "Temp")
        candidates.append(Path("C:/Windows/Temp"))
    else:
        # Unix: prefer TMPDIR, then standard locations
        tmpdir = os.environ.get("TMPDIR")
        if tmpdir:
            candidates.append(Path(tmpdir))
        candidates.extend([
            Path("/tmp"),
            Path("/var/tmp"),
            Path.home() / ".cache" / "claude_hooks_temp",
        ])

    # Find first existing and writable directory
    for candidate in candidates:
        try:
            if candidate.exists() and os.access(str(candidate), os.W_OK):
                log_debug(f"Using temp dir: {candidate}")
                return candidate
        except Exception:
            continue

    # Last resort: create in home directory
    fallback = Path.home() / ".cache" / "claude_hooks_temp"
    fallback.mkdir(parents=True, exist_ok=True)
    log_debug(f"Using fallback temp dir: {fallback}")
    return fallback

# =============================================================================
# CONFIGURATION
# =============================================================================

def get_project_dir() -> Path:
    """Determine the project directory."""
    script_dir = Path(__file__).resolve().parent
    log_debug(f"Script dir: {script_dir}")

    # Strategy 1: Read from .project_path file
    project_path_file = script_dir / ".project_path"
    if project_path_file.exists():
        try:
            recorded_path = project_path_file.read_text(encoding="utf-8-sig").strip()  # utf-8-sig handles BOM
            log_debug(f"Read .project_path: {recorded_path}")
            # Normalize path format for Windows compatibility
            recorded_path = normalize_path(recorded_path)
            recorded_path_obj = Path(recorded_path)
            if recorded_path_obj.exists() and (recorded_path_obj / "config" / "user_preferences.json").exists():
                log_debug(f"Using project dir from .project_path: {recorded_path_obj}")
                return recorded_path_obj
            else:
                log_debug(f"Project path invalid or config missing: {recorded_path_obj}")
        except Exception as e:
            log_error(f"Failed to read .project_path: {e}")

    # Strategy 2: Check if we're in the project structure
    candidate = script_dir.parent
    if (candidate / "config" / "user_preferences.json").exists():
        log_debug(f"Using parent dir as project dir: {candidate}")
        return candidate

    # Strategy 3: Search common locations
    home = Path.home()
    common_locations = [
        home / "claude-code-audio-hooks",
        home / "projects" / "claude-code-audio-hooks",
        home / "Documents" / "claude-code-audio-hooks",
        home / "repos" / "claude-code-audio-hooks",
    ]

    for loc in common_locations:
        if loc.exists() and (loc / "config" / "user_preferences.json").exists():
            log_debug(f"Found project in common location: {loc}")
            return loc

    # Fallback
    log_debug(f"Using fallback project dir: {candidate}")
    return candidate


# Initialize paths
PROJECT_DIR = get_project_dir()
AUDIO_DIR = PROJECT_DIR / "audio"
CONFIG_FILE = PROJECT_DIR / "config" / "user_preferences.json"
QUEUE_DIR = get_safe_temp_dir() / "claude_audio_hooks_queue"
LOCK_FILE = QUEUE_DIR / "audio.lock"

# Ensure queue directory exists
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

# Default audio files for each hook type
DEFAULT_AUDIO_FILES = {
    "notification": "notification-urgent.mp3",
    "stop": "task-complete.mp3",
    "pretooluse": "task-starting.mp3",
    "posttooluse": "task-progress.mp3",
    "userpromptsubmit": "prompt-received.mp3",
    "subagent_stop": "subagent-complete.mp3",
    "precompact": "notification-info.mp3",
    "session_start": "session-start.mp3",
    "session_end": "session-end.mp3",
    "permission_request": "permission-request.mp3",
    "posttoolusefailure": "tool-failed.mp3",
    "subagent_start": "subagent-start.mp3",
    "teammate_idle": "teammate-idle.mp3",
    "task_completed": "team-task-done.mp3",
}

# =============================================================================
# CONFIGURATION FUNCTIONS
# =============================================================================

def load_config() -> Dict[str, Any]:
    """Load configuration from user_preferences.json."""
    if not CONFIG_FILE.exists():
        log_debug(f"Config file not found: {CONFIG_FILE}")
        return {}
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        log_debug(f"Loaded config from {CONFIG_FILE}")
        return config
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in config file: {e}")
        return {}
    except PermissionError as e:
        log_error(f"Permission denied reading config: {e}")
        return {}
    except OSError as e:
        log_error(f"OS error reading config: {e}")
        return {}


def is_hook_enabled(hook_type: str) -> bool:
    """Check if a hook is enabled in configuration."""
    config = load_config()

    # Default enabled hooks
    default_enabled = {"notification", "stop", "subagent_stop", "permission_request"}

    enabled_hooks = config.get("enabled_hooks", {})

    # Check if explicitly set, otherwise use default
    if hook_type in enabled_hooks:
        result = enabled_hooks[hook_type] is True
        log_debug(f"Hook {hook_type} explicitly set to {result}")
        return result

    result = hook_type in default_enabled
    log_debug(f"Hook {hook_type} using default: {result}")
    return result


def get_audio_file(hook_type: str) -> Optional[Path]:
    """Get the audio file path for a hook type."""
    config = load_config()

    # Get configured audio file or use default
    default_file = DEFAULT_AUDIO_FILES.get(hook_type, "notification-info.mp3")
    audio_files = config.get("audio_files", {})
    audio_path = audio_files.get(hook_type, f"default/{default_file}")

    # Build full path
    full_path = AUDIO_DIR / audio_path

    if full_path.exists():
        log_debug(f"Audio file for {hook_type}: {full_path}")
        return full_path

    # Try default location
    default_path = AUDIO_DIR / "default" / default_file
    if default_path.exists():
        log_debug(f"Using default audio for {hook_type}: {default_path}")
        return default_path

    log_debug(f"No audio file found for {hook_type}")
    return None


def get_debounce_ms() -> int:
    """Get debounce time in milliseconds."""
    config = load_config()
    playback_settings = config.get("playback_settings", {})
    return playback_settings.get("debounce_ms", 500)

# =============================================================================
# DEBOUNCE SYSTEM
# =============================================================================

def should_debounce(hook_type: str) -> bool:
    """Check if we should skip this notification due to debounce."""
    debounce_file = QUEUE_DIR / f"{hook_type}_last_played"
    debounce_sec = get_debounce_ms() / 1000.0

    current_time = time.time()

    if debounce_file.exists():
        try:
            last_time = float(debounce_file.read_text(encoding="utf-8").strip())
            if current_time - last_time < debounce_sec:
                log_debug(f"Debouncing {hook_type}: {current_time - last_time:.2f}s < {debounce_sec}s")
                return True
        except (ValueError, OSError) as e:
            log_debug(f"Error reading debounce file: {e}")

    # Update debounce timestamp
    try:
        debounce_file.write_text(str(current_time), encoding="utf-8")
    except OSError as e:
        log_error(f"Failed to write debounce file: {e}")

    return False

# =============================================================================
# AUDIO PLAYBACK FUNCTIONS
# =============================================================================

def play_audio_windows(audio_file: Path) -> bool:
    """Play audio on Windows using multiple fallback methods."""
    # Escape path for PowerShell
    win_path = str(audio_file).replace("\\", "/")
    win_path_escaped = escape_powershell_string(win_path)

    log_debug(f"Windows audio playback: {win_path}")

    # Method 1: Direct PowerShell command with MediaPlayer
    try:
        ps_cmd = (
            'Add-Type -AssemblyName presentationCore; '
            '$p = New-Object System.Windows.Media.MediaPlayer; '
            f'$p.Open("{win_path_escaped}"); '
            'Start-Sleep -Milliseconds 500; '
            '$p.Play(); '
            'Start-Sleep -Seconds 3; '
            '$p.Stop(); $p.Close()'
        )
        proc = subprocess.Popen(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        log_debug(f"Started PowerShell MediaPlayer (PID: {proc.pid})")
        return True
    except FileNotFoundError:
        log_debug("PowerShell not found, trying fallback")
    except Exception as e:
        log_error(f"PowerShell MediaPlayer failed: {e}")

    # Method 2: Use PowerShell script file
    try:
        temp_dir = get_safe_temp_dir()
        script_file = temp_dir / f"claude_audio_{os.getpid()}_{int(time.time())}.ps1"

        ps_script = f'''
Add-Type -AssemblyName presentationCore
$player = New-Object System.Windows.Media.MediaPlayer
$player.Open("{win_path_escaped}")
Start-Sleep -Milliseconds 500
$player.Play()
Start-Sleep -Seconds 3
$player.Stop()
$player.Close()
Remove-Item -Path $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
'''
        script_file.write_text(ps_script, encoding="utf-8")
        log_debug(f"Created PowerShell script: {script_file}")

        proc = subprocess.Popen(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(script_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        log_debug(f"Started PowerShell script (PID: {proc.pid})")
        return True
    except Exception as e:
        log_error(f"PowerShell script method failed: {e}")

    # Method 3: Use WMPlayer.OCX COM object
    try:
        ps_cmd = f'$w = New-Object -ComObject WMPlayer.OCX; $w.URL = "{win_path_escaped}"; Start-Sleep -Seconds 3'
        proc = subprocess.Popen(
            ["powershell.exe", "-Command", ps_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        log_debug(f"Started WMPlayer.OCX (PID: {proc.pid})")
        return True
    except Exception as e:
        log_error(f"WMPlayer.OCX method failed: {e}")
        return False


def play_audio_macos(audio_file: Path) -> bool:
    """Play audio on macOS using afplay."""
    log_debug(f"macOS audio playback: {audio_file}")
    try:
        proc = subprocess.Popen(
            ["afplay", str(audio_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log_debug(f"Started afplay (PID: {proc.pid})")
        return True
    except FileNotFoundError:
        log_error("afplay not found")
        return False
    except Exception as e:
        log_error(f"afplay failed: {e}")
        return False


def play_audio_linux(audio_file: Path) -> bool:
    """Play audio on Linux using available players."""
    log_debug(f"Linux audio playback: {audio_file}")

    players = [
        (["mpg123", "-q"], "mpg123"),
        (["ffplay", "-nodisp", "-autoexit", "-hide_banner", "-loglevel", "quiet"], "ffplay"),
        (["paplay"], "paplay"),
        (["aplay"], "aplay"),
    ]

    for player_cmd, player_name in players:
        try:
            cmd = player_cmd + [str(audio_file)]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            log_debug(f"Started {player_name} (PID: {proc.pid})")
            return True
        except FileNotFoundError:
            log_debug(f"{player_name} not found, trying next")
            continue
        except Exception as e:
            log_debug(f"{player_name} failed: {e}")
            continue

    log_error("No audio player found on Linux")
    return False


def play_audio_wsl(audio_file: Path) -> bool:
    """Play audio in WSL by copying to Windows temp and using PowerShell."""
    log_debug(f"WSL audio playback: {audio_file}")

    try:
        import shutil

        # Get Windows temp directory
        # Try multiple methods to find a writable Windows temp
        win_temp_candidates = []

        # Method 1: Use WSLENV or inherited Windows env vars
        for env_var in ["TEMP", "TMP", "USERPROFILE"]:
            val = os.environ.get(env_var)
            if val and val.startswith("/mnt/"):
                win_temp_candidates.append(Path(val))

        # Method 2: Use wslvar to get Windows TEMP
        try:
            win_temp_path = subprocess.check_output(
                ["wslvar", "TEMP"],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            if win_temp_path:
                # Convert Windows path to WSL path
                wsl_path = subprocess.check_output(
                    ["wslpath", "-u", win_temp_path],
                    text=True,
                    stderr=subprocess.DEVNULL
                ).strip()
                win_temp_candidates.append(Path(wsl_path))
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Method 3: Standard Windows temp locations via /mnt
        windir = os.environ.get("WINDIR", "")
        if windir and windir.startswith("/mnt/"):
            win_temp_candidates.append(Path(windir) / "Temp")

        win_temp_candidates.extend([
            Path("/mnt/c/Windows/Temp"),
            Path("/mnt/c/Users") / os.environ.get("USER", "Public") / "AppData/Local/Temp",
        ])

        # Find first writable temp directory
        win_temp = None
        for candidate in win_temp_candidates:
            try:
                if candidate.exists() and os.access(str(candidate), os.W_OK):
                    win_temp = candidate
                    break
            except Exception:
                continue

        if not win_temp:
            log_error("Could not find writable Windows temp directory from WSL")
            # Fallback to native Linux playback
            return play_audio_linux(audio_file)

        log_debug(f"Using Windows temp: {win_temp}")

        # Copy audio file to Windows temp
        temp_filename = f"claude_audio_{int(time.time())}_{os.getpid()}.mp3"
        wsl_temp_file = win_temp / temp_filename
        shutil.copy(str(audio_file), str(wsl_temp_file))
        log_debug(f"Copied audio to: {wsl_temp_file}")

        # Convert to Windows path for PowerShell
        try:
            win_path = subprocess.check_output(
                ["wslpath", "-w", str(wsl_temp_file)],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Manual conversion
            path_str = str(wsl_temp_file)
            if path_str.startswith("/mnt/"):
                drive = path_str[5].upper()
                win_path = f"{drive}:{path_str[6:]}".replace("/", "\\")
            else:
                log_error("Could not convert WSL path to Windows path")
                return play_audio_linux(audio_file)

        log_debug(f"Windows path: {win_path}")
        win_path_escaped = escape_powershell_string(win_path.replace("\\", "/"))

        # Play using PowerShell
        ps_command = f'''
Add-Type -AssemblyName presentationCore
$player = New-Object System.Windows.Media.MediaPlayer
$player.Open("{win_path_escaped}")
Start-Sleep -Milliseconds 500
$player.Play()
Start-Sleep -Seconds 4
$player.Stop()
$player.Close()
Remove-Item -Path "{win_path_escaped}" -ErrorAction SilentlyContinue
'''

        proc = subprocess.Popen(
            ["powershell.exe", "-Command", ps_command],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log_debug(f"Started WSL PowerShell playback (PID: {proc.pid})")
        return True

    except Exception as e:
        log_error(f"WSL audio playback failed: {e}")
        # Fallback to native Linux playback
        log_debug("Falling back to native Linux playback")
        return play_audio_linux(audio_file)


def is_wsl() -> bool:
    """Check if running in WSL."""
    try:
        with open("/proc/version", "r") as f:
            content = f.read().lower()
            return "microsoft" in content or "wsl" in content
    except (FileNotFoundError, PermissionError):
        return False


def play_audio(audio_file: Path) -> bool:
    """Play audio file using platform-specific method."""
    system = platform.system()
    log_debug(f"Platform: {system}")

    if system == "Windows":
        return play_audio_windows(audio_file)
    elif system == "Darwin":
        return play_audio_macos(audio_file)
    elif system == "Linux":
        if is_wsl():
            log_debug("Detected WSL environment")
            return play_audio_wsl(audio_file)
        return play_audio_linux(audio_file)
    else:
        log_error(f"Unsupported platform: {system}")
        return False

# =============================================================================
# STDIN PARSING
# =============================================================================

def parse_stdin() -> dict:
    """Parse JSON data from Claude Code via stdin."""
    try:
        raw = sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
            log_debug(f"Parsed stdin JSON: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return data if isinstance(data, dict) else {}
    except json.JSONDecodeError as e:
        log_debug(f"stdin was not valid JSON: {e}")
    except Exception as e:
        log_debug(f"Failed to read stdin: {e}")
    return {}

# =============================================================================
# CONTEXT EXTRACTION
# =============================================================================

def get_notification_context(hook_type: str, stdin_data: dict) -> str:
    """Generate human-readable context from hook data."""
    if hook_type == "stop":
        return "Task completed"
    elif hook_type == "notification":
        msg = stdin_data.get("message", "")
        return "Authorization needed" + (f": {msg[:80]}" if msg else "")
    elif hook_type == "pretooluse":
        tool = stdin_data.get("tool_name", "unknown")
        return f"Running: {tool}"
    elif hook_type == "posttooluse":
        tool = stdin_data.get("tool_name", "unknown")
        return f"Completed: {tool}"
    elif hook_type == "subagent_stop":
        agent = stdin_data.get("agent_type", "")
        return "Background task finished" + (f" ({agent})" if agent else "")
    elif hook_type == "session_start":
        return "Session started"
    elif hook_type == "session_end":
        return "Session ended"
    elif hook_type == "precompact":
        return "Compacting context"
    elif hook_type == "userpromptsubmit":
        return "Prompt received"
    elif hook_type == "permission_request":
        tool = stdin_data.get("tool_name", "unknown")
        return f"Permission needed: {tool}"
    elif hook_type == "posttoolusefailure":
        tool = stdin_data.get("tool_name", "unknown")
        error = stdin_data.get("error", "")
        return f"Tool failed: {tool}" + (f" - {error[:60]}" if error else "")
    elif hook_type == "subagent_start":
        agent_type = stdin_data.get("agent_type", "")
        return f"Subagent starting" + (f": {agent_type}" if agent_type else "")
    elif hook_type == "teammate_idle":
        teammate = stdin_data.get("teammate_name", "unknown")
        team = stdin_data.get("team_name", "")
        return f"Teammate idle: {teammate}" + (f" ({team})" if team else "")
    elif hook_type == "task_completed":
        subject = stdin_data.get("task_subject", "")
        return f"Task completed" + (f": {subject[:60]}" if subject else "")
    return hook_type.replace("_", " ").title()

# =============================================================================
# DESKTOP NOTIFICATIONS
# =============================================================================

def _escape_notification_string(s: str) -> str:
    """Escape a string for safe use in notification commands."""
    # Remove characters that could cause shell/osascript injection
    return s.replace('"', '\\"').replace("'", "\\'").replace('`', '').replace('$', '')


def send_desktop_notification(title: str, message: str, urgency: str = "normal") -> bool:
    """Send a desktop notification using platform-native methods.

    Args:
        title: Notification title
        message: Notification body text
        urgency: 'normal' or 'critical'

    Returns:
        True if notification was dispatched, False otherwise
    """
    system = platform.system()
    safe_title = _escape_notification_string(title)
    safe_message = _escape_notification_string(message)

    try:
        if system == "Darwin":
            # Audio is handled separately by play_audio_macos() via afplay.
            # Omit "sound name" to avoid double sound and to work on macOS 15+
            # where osascript notifications may be silently blocked.
            script = f'display notification "{safe_message}" with title "{safe_title}"'
            subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            log_debug(f"Sent macOS notification: {title} - {message}")
            return True

        elif system == "Linux":
            if is_wsl():
                # WSL: use PowerShell NotifyIcon balloon tip (non-blocking toast)
                ps_cmd = (
                    '[void][System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); '
                    '$n = New-Object System.Windows.Forms.NotifyIcon; '
                    '$n.Icon = [System.Drawing.SystemIcons]::Information; '
                    '$n.Visible = $true; '
                    f'$n.ShowBalloonTip(5000, "{safe_title}", "{safe_message}", '
                    f'[System.Windows.Forms.ToolTipIcon]::{"Warning" if urgency == "critical" else "Info"}); '
                    'Start-Sleep -Seconds 6; '
                    '$n.Dispose()'
                )
                subprocess.Popen(
                    ["powershell.exe", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                log_debug(f"Sent WSL balloon notification via PowerShell: {title}")
                return True
            else:
                # Native Linux: use notify-send
                if shutil.which("notify-send"):
                    cmd = ["notify-send"]
                    if urgency == "critical":
                        cmd.extend(["-u", "critical"])
                    cmd.extend([title, message])
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    log_debug(f"Sent Linux notification: {title} - {message}")
                    return True
                else:
                    log_debug("notify-send not found, skipping desktop notification")
                    return False

        elif system == "Windows":
            # Windows: use NotifyIcon balloon tip (non-blocking toast)
            ps_cmd = (
                '[void][System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); '
                '$n = New-Object System.Windows.Forms.NotifyIcon; '
                '$n.Icon = [System.Drawing.SystemIcons]::Information; '
                '$n.Visible = $true; '
                f'$n.ShowBalloonTip(5000, "{safe_title}", "{safe_message}", '
                f'[System.Windows.Forms.ToolTipIcon]::{"Warning" if urgency == "critical" else "Info"}); '
                'Start-Sleep -Seconds 6; '
                '$n.Dispose()'
            )
            subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            log_debug(f"Sent Windows balloon notification: {title}")
            return True

    except FileNotFoundError as e:
        log_debug(f"Notification command not found: {e}")
    except Exception as e:
        log_error(f"Desktop notification failed: {e}")

    return False

# =============================================================================
# TEXT-TO-SPEECH
# =============================================================================

def play_tts(message: str) -> bool:
    """Speak a message using platform-native TTS.

    Args:
        message: Text to speak

    Returns:
        True if TTS was dispatched, False otherwise
    """
    system = platform.system()
    # Sanitize message for shell safety
    safe_message = _escape_notification_string(message)

    try:
        if system == "Darwin":
            subprocess.Popen(
                ["say", message],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            log_debug(f"TTS (macOS say): {message}")
            return True

        elif system == "Linux":
            if is_wsl():
                # WSL: use Windows SAPI via PowerShell
                ps_cmd = (
                    'Add-Type -AssemblyName System.Speech; '
                    f'(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{safe_message}")'
                )
                subprocess.Popen(
                    ["powershell.exe", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                log_debug(f"TTS (WSL PowerShell): {message}")
                return True
            else:
                # Native Linux: try espeak, then spd-say
                for cmd_name in ["espeak", "spd-say"]:
                    if shutil.which(cmd_name):
                        subprocess.Popen(
                            [cmd_name, message],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        log_debug(f"TTS (Linux {cmd_name}): {message}")
                        return True
                log_debug("No Linux TTS engine found (espeak, spd-say)")
                return False

        elif system == "Windows":
            ps_cmd = (
                'Add-Type -AssemblyName System.Speech; '
                f'(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{safe_message}")'
            )
            subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            log_debug(f"TTS (Windows SAPI): {message}")
            return True

    except FileNotFoundError as e:
        log_debug(f"TTS command not found: {e}")
    except Exception as e:
        log_error(f"TTS failed: {e}")

    return False

# =============================================================================
# MAIN HOOK EXECUTION
# =============================================================================

def run_hook(hook_type: str, stdin_data: dict = None) -> int:
    """
    Main hook execution function.

    Returns:
        0 on success (hook executed or disabled)
        Non-zero on error
    """
    log_debug(f"=== Running hook: {hook_type} ===")
    log_debug(f"Project dir: {PROJECT_DIR}")
    log_debug(f"Audio dir: {AUDIO_DIR}")
    log_debug(f"Queue dir: {QUEUE_DIR}")

    # Check if hook is enabled
    if not is_hook_enabled(hook_type):
        log_trigger(hook_type, "DISABLED")
        return 0

    # Check debounce
    if should_debounce(hook_type):
        log_trigger(hook_type, "DEBOUNCED")
        return 0

    # Load config once for notification/TTS settings
    config = load_config()

    # Determine notification mode (backward compatible: default to audio_only)
    notification_settings = config.get("notification_settings", {})
    mode = notification_settings.get("mode", "audio_only")

    # Play audio (unless mode is notification_only)
    if mode in ("audio_only", "audio_and_notification"):
        audio_file = get_audio_file(hook_type)
        if not audio_file:
            log_trigger(hook_type, "NO_AUDIO_CONFIG")
        elif not audio_file.exists():
            log_trigger(hook_type, "FILE_NOT_FOUND", str(audio_file))
            log_error(f"Audio file not found: {audio_file}")
        else:
            success = play_audio(audio_file)
            if success:
                log_trigger(hook_type, "PLAYED", audio_file.name)
            else:
                log_trigger(hook_type, "PLAY_FAILED", audio_file.name)
                log_error(f"Failed to play audio: {audio_file}")
    elif mode == "notification_only":
        log_trigger(hook_type, "AUDIO_SKIPPED", f"mode={mode}")

    # Desktop notification
    if mode in ("notification_only", "audio_and_notification"):
        context = get_notification_context(hook_type, stdin_data or {})
        urgency = "critical" if hook_type in ("notification", "permission_request", "posttoolusefailure") else "normal"
        notif_sent = send_desktop_notification("Claude Code", context, urgency)
        if notif_sent:
            log_debug(f"Desktop notification sent for {hook_type}: {context}")

    # TTS (text-to-speech)
    tts_settings = config.get("tts_settings", {})
    if tts_settings.get("enabled", False):
        context = get_notification_context(hook_type, stdin_data or {})
        custom_messages = tts_settings.get("messages", {})
        tts_message = custom_messages.get(hook_type, context)
        tts_sent = play_tts(tts_message)
        if tts_sent:
            log_debug(f"TTS played for {hook_type}: {tts_message}")

    return 0


def main() -> int:
    """Main entry point."""
    # Check Python version
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required", file=sys.stderr)
        return 1

    if len(sys.argv) < 2:
        print("Usage: python hook_runner.py <hook_type>", file=sys.stderr)
        print("Hook types: notification, stop, pretooluse, posttooluse, posttoolusefailure,", file=sys.stderr)
        print("            userpromptsubmit, subagent_stop, subagent_start, precompact,", file=sys.stderr)
        print("            session_start, session_end, permission_request,", file=sys.stderr)
        print("            teammate_idle, task_completed", file=sys.stderr)
        print("\nEnvironment variables:", file=sys.stderr)
        print("  CLAUDE_HOOKS_DEBUG=1  Enable debug logging", file=sys.stderr)
        return 1

    hook_type = sys.argv[1].lower().replace("-", "_")

    log_debug(f"Hook runner started: {hook_type}")
    log_debug(f"Python version: {sys.version}")
    log_debug(f"Platform: {platform.system()} {platform.release()}")

    # Parse stdin JSON from Claude Code (provides context about the hook event)
    stdin_data = parse_stdin()

    return run_hook(hook_type, stdin_data)


if __name__ == "__main__":
    sys.exit(main())
