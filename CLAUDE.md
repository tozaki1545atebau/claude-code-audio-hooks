# Claude Code Audio Hooks - AI Assistant Guide

> **Version:** 4.0.0 | **Last Updated:** 2026-02-10

This document is designed for AI assistants (Claude Code, Cursor, Copilot, etc.) to understand and help users install this project correctly.

## Project Overview

**Claude Code Audio Hooks** provides audio notifications for Claude Code CLI events. When Claude completes tasks, triggers notifications, or needs authorization, users hear audio cues instead of constantly watching the terminal.

```mermaid
graph LR
    A[Claude Code CLI] -->|Triggers Hook| B[Hook System]
    B -->|Reads Config| C[user_preferences.json]
    C -->|Selects Audio| D[Audio Files]
    D -->|Plays via| E{Platform Player}
    E -->|Windows| F[PowerShell MediaPlayer]
    E -->|macOS| G[afplay]
    E -->|Linux| H[mpg123/ffplay/aplay]
```

## Quick Reference: Installation Commands

### Quick Setup (Lite - Recommended First)
Zero dependencies, zero Python. Single command:
```bash
curl -sL https://raw.githubusercontent.com/ChanMeng666/claude-code-audio-hooks/master/scripts/quick-setup.sh | bash
```
Gives: desktop notifications + system sounds for Stop, Notification, SubagentStop hooks.

### Full Install (Standard/Pro)

| Platform | Command |
|----------|---------|
| **Windows (PowerShell)** | `.\scripts\install-windows.ps1` |
| **Windows (Git Bash)** | `bash scripts/install-complete.sh` |
| **WSL** | `bash scripts/install-complete.sh` |
| **macOS** | `bash scripts/install-complete.sh` |
| **Linux** | `bash scripts/install-complete.sh` |

Gives: custom MP3 audio + desktop notifications + context-aware alerts + TTS (optional).

## Platform Detection Decision Tree

Use this decision tree to determine the correct installation method:

```mermaid
flowchart TD
    Start([User wants to install]) --> Q1{What OS?}

    Q1 -->|Windows| Q2{Which shell?}
    Q1 -->|macOS| MAC[Use: bash scripts/install-complete.sh]
    Q1 -->|Linux| LINUX[Use: bash scripts/install-complete.sh]

    Q2 -->|PowerShell/CMD| WIN_PS[Use: .\scripts\install-windows.ps1]
    Q2 -->|Git Bash| WIN_GB[Use: bash scripts/install-complete.sh]
    Q2 -->|WSL| WSL[Use: bash scripts/install-complete.sh]
    Q2 -->|Cygwin| CYG[Use: bash scripts/install-complete.sh]

    MAC --> CHECK[Check Python 3.6+]
    LINUX --> CHECK
    WIN_PS --> CHECK
    WIN_GB --> CHECK
    WSL --> CHECK
    CYG --> CHECK

    CHECK --> INSTALL[Run installer]
    INSTALL --> RESTART[Restart Claude Code]
    RESTART --> TEST[Test: claude 'What is 2+2?']
```

## Project Structure

```
claude-code-audio-hooks/
├── CLAUDE.md                    # THIS FILE - AI assistant guide
├── README.md                    # User documentation
├── CHANGELOG.md                 # Version history
│
├── audio/
│   └── default/                 # Audio files (9 MP3 files)
│       ├── notification.mp3     # Authorization requests
│       ├── task-complete.mp3    # Task completion (Stop)
│       ├── session-start.mp3    # Session begins
│       ├── session-end.mp3      # Session ends
│       ├── tool-start.mp3       # Before tool execution
│       ├── tool-end.mp3         # After tool execution
│       ├── user-prompt.mp3      # User submits prompt
│       ├── subagent-complete.mp3# Background task done
│       └── compact.mp3          # Context compaction
│
├── config/
│   ├── default_preferences.json # Default settings template
│   └── user_preferences.json    # User's active settings
│
├── hooks/
│   ├── hook_runner.py           # Main Python hook runner (Windows)
│   └── shared/
│       └── hook_config.sh       # Shared bash functions (macOS/Linux)
│
├── scripts/
│   ├── quick-setup.sh           # Lite tier installer (zero deps, curl | bash)
│   ├── quick-unsetup.sh         # Lite tier uninstaller
│   ├── install-complete.sh      # Full installer (all platforms)
│   ├── install-windows.ps1      # PowerShell installer (Windows)
│   ├── uninstall.sh             # Uninstaller
│   ├── configure.sh             # Configuration utility
│   ├── test-audio.sh            # Audio testing tool
│   └── diagnose.py              # Diagnostic tool
│
└── docs/                        # Detailed documentation
    ├── ARCHITECTURE.md          # System architecture
    ├── INSTALLATION_GUIDE.md    # Detailed installation guide
    └── TROUBLESHOOTING.md       # Problem solving guide
```

## Hook Types and Audio Mapping

```mermaid
graph TD
    subgraph "Hook Events"
        H1[Notification] -->|"Authorization needed"| A1[notification.mp3]
        H2[Stop] -->|"Task completed"| A2[task-complete.mp3]
        H3[SessionStart] -->|"Session begins"| A3[session-start.mp3]
        H4[SessionEnd] -->|"Session ends"| A4[session-end.mp3]
        H5[PreToolUse] -->|"Before tool"| A5[tool-start.mp3]
        H6[PostToolUse] -->|"After tool"| A6[tool-end.mp3]
        H7[UserPromptSubmit] -->|"User input"| A7[user-prompt.mp3]
        H8[SubagentStop] -->|"Background done"| A8[subagent-complete.mp3]
        H9[PreCompact] -->|"Compacting"| A9[compact.mp3]
    end
```

| Hook | Trigger | Default Audio | Recommended |
|------|---------|---------------|-------------|
| `Notification` | Authorization requests | notification.mp3 | **Enable** |
| `Stop` | Task completion | task-complete.mp3 | **Enable** |
| `SubagentStop` | Background task done | subagent-complete.mp3 | **Enable** |
| `SessionStart` | New session begins | session-start.mp3 | Optional |
| `SessionEnd` | Session closes | session-end.mp3 | Optional |
| `PreToolUse` | Before each tool | tool-start.mp3 | Disable (noisy) |
| `PostToolUse` | After each tool | tool-end.mp3 | Disable (noisy) |
| `UserPromptSubmit` | User sends message | user-prompt.mp3 | Optional |
| `PreCompact` | Context compaction | compact.mp3 | Optional |

## Installation Prerequisites

### All Platforms
- **Claude Code CLI** - Must be installed and working
- **Python 3.6+** - Required for hook execution

### Platform-Specific

| Platform | Audio Player | Notes |
|----------|--------------|-------|
| Windows | PowerShell MediaPlayer | Built-in, no install needed |
| macOS | afplay | Built-in, no install needed |
| Linux | mpg123, ffplay, or aplay | May need: `sudo apt install mpg123` |
| WSL | PowerShell (via Windows) | Audio plays through Windows |

## Installation Flow

```mermaid
sequenceDiagram
    participant User
    participant Installer
    participant Claude as ~/.claude/
    participant Project as Project Dir

    User->>Installer: Run install script
    Installer->>Installer: Detect platform
    Installer->>Installer: Check prerequisites
    Installer->>Claude: Create hooks/ directory
    Installer->>Claude: Copy hook_runner.py
    Installer->>Claude: Save .project_path
    Installer->>Claude: Configure settings.json
    Installer->>Project: Create user_preferences.json
    Installer->>User: Installation complete
    User->>User: Restart Claude Code
    User->>Claude: Test with "claude 'test'"
```

## Key Files After Installation

### ~/.claude/settings.json
```json
{
  "hooks": {
    "Notification": [{"hooks": [{"type": "command", "command": "py \"~/.claude/hooks/hook_runner.py\" notification"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "py \"~/.claude/hooks/hook_runner.py\" stop"}]}],
    // ... 7 more hooks
  }
}
```

### ~/.claude/hooks/.project_path
Contains the absolute path to the project directory (Windows format on Windows):
```
D:/github_repository/claude-code-audio-hooks
```

### config/user_preferences.json
```json
{
  "enabled_hooks": {
    "notification": true,
    "stop": true,
    "subagent_stop": true,
    "session_start": false,
    "session_end": false,
    "pretooluse": false,
    "posttooluse": false,
    "userpromptsubmit": false,
    "precompact": false
  },
  "notification_settings": {
    "mode": "audio_and_notification",
    "show_context": true
  },
  "tts_settings": {
    "enabled": false,
    "messages": {
      "stop": "Task completed",
      "notification": "Attention, authorization needed"
    }
  }
}
```

## Troubleshooting Quick Reference

### Enable Debug Logging
```bash
# Bash/Zsh (Linux/macOS/Git Bash/WSL)
export CLAUDE_HOOKS_DEBUG=1

# PowerShell
$env:CLAUDE_HOOKS_DEBUG = "1"
```

### Run Diagnostics
```bash
python scripts/diagnose.py -v --test-audio
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No audio after install | Didn't restart Claude | Restart terminal/Claude Code |
| Path errors on Windows | Git Bash path format | Re-run installer (auto-converts) |
| WSL no audio | PowerShell not accessible | Check `powershell.exe` works |
| Linux no audio | No audio player | Install: `sudo apt install mpg123` |
| "Invalid Settings" error | Old hooks format | Re-run installer for new format |

### Log Locations

| Platform | Log Directory |
|----------|---------------|
| Windows | `%TEMP%\claude_audio_hooks_queue\logs\` |
| Linux/macOS | `/tmp/claude_audio_hooks_queue/logs/` |
| WSL | `/tmp/claude_audio_hooks_queue/logs/` |

## For AI Assistants: Installation Steps

When a user asks to install this project, **recommend Quick Setup first** unless they specifically need custom audio or TTS.

### Option A: Quick Setup (Recommended)

```bash
curl -sL https://raw.githubusercontent.com/ChanMeng666/claude-code-audio-hooks/master/scripts/quick-setup.sh | bash
```

Then instruct user to restart Claude Code.

### Option B: Full Install (Custom Audio / TTS / Advanced Features)

#### Step 1: Detect Environment
```bash
# Check OS
uname -s  # Linux, Darwin (macOS), or MINGW*/MSYS* (Git Bash)

# Check for WSL
cat /proc/version 2>/dev/null | grep -i microsoft

# Check Python
python3 --version || python --version || py --version
```

#### Step 2: Clone Repository
```bash
git clone https://github.com/ChanMeng666/claude-code-audio-hooks.git
cd claude-code-audio-hooks
```

#### Step 3: Run Appropriate Installer

**Windows PowerShell:**
```powershell
.\scripts\install-windows.ps1
```

**All other platforms (Git Bash, WSL, macOS, Linux):**
```bash
bash scripts/install-complete.sh
```

#### Step 4: Verify Installation
```bash
# Check hook runner installed
ls -la ~/.claude/hooks/hook_runner.py

# Check settings configured
cat ~/.claude/settings.json | grep hook_runner

# Check project path saved
cat ~/.claude/hooks/.project_path
```

#### Step 5: Test
Instruct user to:
1. Restart Claude Code (close and reopen terminal)
2. Run: `claude "What is 2+2?"`
3. Listen for audio when response completes

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| 4.0.0 | 2026-02-10 | Quick Setup (Lite tier), desktop notifications, TTS, context-aware alerts |
| 3.3.5 | 2025-12-27 | UTF-8 BOM fix for Windows |
| 3.3.4 | 2025-12-22 | Windows PowerShell installer, diagnostic tool, debug logging |
| 3.3.3 | 2025-11-07 | WSL audio fix, hooks format fix |
| 3.3.0 | 2025-11-06 | Non-interactive mode for all scripts |
| 3.0.0 | 2025-11-05 | Complete rewrite, Python hook runner |

## Related Documentation

- [README.md](README.md) - Full user documentation
- [CHANGELOG.md](CHANGELOG.md) - Detailed version history
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture details
- [docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md) - Step-by-step installation
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Problem solving guide

---

*This document is optimized for AI assistant consumption. For human-readable documentation, see [README.md](README.md).*
