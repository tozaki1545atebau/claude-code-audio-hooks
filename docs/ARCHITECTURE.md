# System Architecture

> **Version:** 4.5.0 | **Last Updated:** 2026-03-22

This document explains the technical architecture of Claude Code Audio Hooks.

## System Overview

```mermaid
graph TB
    subgraph "Claude Code CLI"
        CC[Claude Code] -->|Triggers| HE[Hook Events]
    end

    subgraph "Hook System"
        HE -->|Reads| SJ[~/.claude/settings.json]
        SJ -->|Executes| HR[hook_runner.py]
        HR -->|Reads| PP[.project_path]
        PP -->|Points to| PD[Project Directory]
    end

    subgraph "Project Directory"
        PD --> UP[config/user_preferences.json]
        PD --> AD[audio/default/*.mp3]
        UP -->|Determines| EN[Enabled Hooks]
        AD -->|Provides| AF[Audio Files]
    end

    subgraph "Audio Playback"
        HR -->|Checks| EN
        EN -->|If enabled| AP{Audio Player}
        AF --> AP
        AP -->|Windows| PS[PowerShell MediaPlayer]
        AP -->|macOS| AFP[afplay]
        AP -->|Linux| MPG[mpg123/ffplay/aplay]
    end

    subgraph "Logging"
        HR -->|Writes| TL[Trigger Logs]
        HR -->|If DEBUG| DL[Debug Logs]
        TL --> LD[logs/hook_triggers.log]
        DL --> LDD[logs/debug.log]
    end
```

## Component Details

### 1. Claude Code CLI Integration

Claude Code provides a hooks system that executes commands at specific lifecycle events.

**Hook Configuration Location:** `~/.claude/settings.json`

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "py \"C:/Users/username/.claude/hooks/hook_runner.py\" stop"
          }
        ]
      }
    ]
  }
}
```

**Hook Types:**

| Hook | When Triggered | Use Case |
|------|---------------|----------|
| `Notification` | Authorization required | Alert user to approve action |
| `Stop` | Task completed | Notify task is done |
| `SessionStart` | New session begins | Mark session start |
| `SessionEnd` | Session closes | Mark session end |
| `PreToolUse` | Before tool execution | Pre-action notification |
| `PostToolUse` | After tool execution | Post-action notification |
| `UserPromptSubmit` | User sends message | Acknowledge input |
| `SubagentStop` | Background task done | Notify subagent completion |
| `PermissionRequest` | Permission dialog appears | Alert user to approve command |
| `PostToolUseFailure` | Tool execution fails | Alert user of tool failure |
| `SubagentStart` | Subagent spawned | Notify subagent start |
| `TeammateIdle` | Teammate goes idle | Notify teammate idle |
| `TaskCompleted` | Team task completed | Notify task completion |
| `PreCompact` | Context compaction | Notify memory optimization |
| `StopFailure` | API error (rate limit, auth, etc.) | Alert user of API failure |
| `PostCompact` | After compaction completes | Confirm compaction done |
| `ConfigChange` | Configuration file changed | Notify config update |
| `InstructionsLoaded` | CLAUDE.md/rules loaded | Notify instructions loaded |
| `WorktreeCreate` | Worktree created | Notify isolation worktree created |
| `WorktreeRemove` | Worktree removed | Notify worktree cleanup |
| `Elicitation` | MCP server requests input | Alert user to respond |
| `ElicitationResult` | Elicitation response sent | Confirm response submitted |

### 2. Hook Runner (Python)

**File:** `~/.claude/hooks/hook_runner.py`

The hook runner is the central execution component that:
1. Receives hook type as command-line argument
2. Reads project path from `.project_path`
3. Loads user preferences
4. Determines if hook is enabled
5. Selects appropriate audio file
6. Plays audio via platform-specific method

```mermaid
sequenceDiagram
    participant CC as Claude Code
    participant HR as hook_runner.py
    participant PP as .project_path
    participant UP as user_preferences.json
    participant AP as Audio Player

    CC->>HR: Execute with hook type + JSON stdin
    HR->>HR: Check snooze status
    HR->>PP: Read project path
    PP-->>HR: Return path
    HR->>HR: Normalize path (Git Bash/WSL/Cygwin)
    HR->>UP: Load preferences
    UP-->>HR: Return enabled hooks + notification mode
    HR->>HR: Check if hook enabled
    HR->>HR: Check debounce
    alt Hook Enabled & Not Snoozed
        HR->>HR: Determine notification mode (per-hook or global)
        alt Audio Mode (audio_only or audio_and_notification)
            HR->>HR: Select audio file (theme-aware)
            HR->>AP: Play audio
            AP-->>HR: Playback complete
        end
        alt Notification Mode (notification_only or audio_and_notification)
            HR->>HR: Parse stdin JSON for context
            HR->>HR: Send desktop notification
        end
        alt TTS Enabled
            HR->>HR: Speak context-aware message
        end
    end
    HR->>HR: Log trigger event
```

**Path Normalization:**

The hook runner handles multiple path formats:

| Source | Format | Example |
|--------|--------|---------|
| Git Bash | `/d/path/to/project` | `/d/github_repository/project` |
| WSL2 | `/mnt/c/path/to/project` | `/mnt/c/Users/name/project` |
| Cygwin | `/cygdrive/c/path` | `/cygdrive/c/Users/name/project` |
| Windows | `D:/path/to/project` | `D:/github_repository/project` |

### 3. Audio Playback System

```mermaid
flowchart TD
    subgraph "Platform Detection"
        PD[Detect Platform] --> WIN{Windows?}
        WIN -->|Yes| WSL{WSL?}
        WIN -->|No| MAC{macOS?}
        WSL -->|Yes| PS_WSL[PowerShell via WSL]
        WSL -->|No| PS_WIN[PowerShell Direct]
        MAC -->|Yes| AFP[afplay]
        MAC -->|No| LINUX[Linux Players]
    end

    subgraph "Windows Playback"
        PS_WIN --> MP[MediaPlayer API]
        PS_WSL -->|Copy to temp| TEMP[Windows Temp]
        TEMP --> MP
        MP --> PLAY[Play Audio]
    end

    subgraph "macOS Playback"
        AFP --> PLAY
    end

    subgraph "Linux Playback"
        LINUX --> MPG123{mpg123?}
        MPG123 -->|Yes| PLAY
        MPG123 -->|No| FFPLAY{ffplay?}
        FFPLAY -->|Yes| PLAY
        FFPLAY -->|No| APLAY[aplay]
        APLAY --> PLAY
    end
```

**Windows PowerShell Command:**
```powershell
Add-Type -AssemblyName presentationCore
$mediaPlayer = New-Object System.Windows.Media.MediaPlayer
$mediaPlayer.Open("D:/project/audio/default/task-complete.mp3")
Start-Sleep -Milliseconds 500
$mediaPlayer.Play()
Start-Sleep -Seconds 2
$mediaPlayer.Stop()
$mediaPlayer.Close()
```

**macOS Command:**
```bash
afplay /path/to/audio/task-complete.mp3
```

**Linux Command:**
```bash
mpg123 -q /path/to/audio/task-complete.mp3
```

### 4. Configuration System

```mermaid
graph LR
    subgraph "Configuration Files"
        DP[default_preferences.json] -->|Template| UP[user_preferences.json]
        SJ[settings.json] -->|Hook Commands| CC[Claude Code]
        PP[.project_path] -->|Project Location| HR[hook_runner.py]
    end

    subgraph "Runtime Flow"
        HR -->|Reads| PP
        HR -->|Loads| UP
        UP -->|Determines| EH[Enabled Hooks]
        UP -->|Selects| TH[Audio Theme]
    end
```

**user_preferences.json Structure:**
```json
{
  "_comment": "User preferences for audio hooks",
  "enabled_hooks": {
    "_description": "Enable/disable individual hooks",
    "notification": true,
    "stop": true,
    "subagent_stop": true,
    "permission_request": true,
    "session_start": false,
    "session_end": false,
    "pretooluse": false,
    "posttooluse": false,
    "posttoolusefailure": false,
    "userpromptsubmit": false,
    "precompact": false,
    "subagent_start": false,
    "teammate_idle": false,
    "task_completed": false,
    "stop_failure": false,
    "postcompact": false,
    "config_change": false,
    "instructions_loaded": false,
    "worktree_create": false,
    "worktree_remove": false,
    "elicitation": false,
    "elicitation_result": false
  },
  "audio_settings": {
    "theme": "default",
    "volume": 1.0
  },
  "playback_settings": {
    "queue_enabled": true,
    "max_queue_size": 5,
    "debounce_ms": 500
  }
}
```

### 5. Logging System

```mermaid
graph TD
    subgraph "Log Types"
        TL[Trigger Log] -->|Always| TLF[hook_triggers.log]
        DL[Debug Log] -->|CLAUDE_HOOKS_DEBUG=1| DLF[debug.log]
        IL[Install Log] -->|During install| ILF[claude_hooks_install_*.log]
    end

    subgraph "Log Locations"
        WIN_TEMP[Windows: %TEMP%/claude_audio_hooks_queue/logs/]
        UNIX_TEMP[Unix: /tmp/claude_audio_hooks_queue/logs/]
    end

    TLF --> WIN_TEMP
    TLF --> UNIX_TEMP
    DLF --> WIN_TEMP
    DLF --> UNIX_TEMP
```

**Trigger Log Format:**
```
2025-12-22 14:30:45 | stop | task-complete.mp3
2025-12-22 14:31:02 | notification | notification.mp3
```

**Debug Log Format:**
```
2025-12-22 14:30:45 | DEBUG | Hook triggered: stop
2025-12-22 14:30:45 | DEBUG | Project path: D:/github_repository/claude-code-audio-hooks
2025-12-22 14:30:45 | DEBUG | Audio file: D:/github_repository/claude-code-audio-hooks/audio/default/task-complete.mp3
2025-12-22 14:30:45 | DEBUG | Playing via PowerShell...
2025-12-22 14:30:47 | DEBUG | Playback complete
```

## Installation Architecture

```mermaid
sequenceDiagram
    participant User
    participant Script as Installer Script
    participant Home as ~/.claude/
    participant Project as Project Dir
    participant Settings as settings.json

    User->>Script: Run installer
    Script->>Script: Detect platform
    Script->>Script: Verify prerequisites

    Script->>Home: mkdir -p hooks/
    Script->>Home: Copy hook_runner.py
    Script->>Home: Write .project_path

    Script->>Settings: Backup existing
    Script->>Settings: Add hook configurations

    Script->>Project: Copy default_preferences.json
    Note over Project: Creates user_preferences.json

    Script->>Script: Run validation tests
    Script->>User: Report success/failure
```

## Cross-Platform Compatibility

### Platform Detection Logic

```mermaid
flowchart TD
    START[Start] --> CHECK_OS{platform.system()}

    CHECK_OS -->|Windows| CHECK_WSL{Check /proc/version}
    CHECK_OS -->|Linux| CHECK_WSL2{Contains 'microsoft'?}
    CHECK_OS -->|Darwin| MACOS[macOS Detected]

    CHECK_WSL -->|Contains 'microsoft'| WSL[WSL Detected]
    CHECK_WSL -->|Otherwise| CHECK_MSYS{OSTYPE contains 'msys'?}

    CHECK_WSL2 -->|Yes| WSL
    CHECK_WSL2 -->|No| LINUX[Linux Detected]

    CHECK_MSYS -->|Yes| GITBASH[Git Bash Detected]
    CHECK_MSYS -->|No| WINDOWS[Windows Native Detected]
```

### Path Handling by Platform

| Platform | Input Path | Normalized Path |
|----------|-----------|-----------------|
| Windows Native | `D:\project\audio` | `D:/project/audio` |
| Git Bash | `/d/project/audio` | `D:/project/audio` |
| WSL | `/mnt/c/project/audio` | `C:/project/audio` |
| Cygwin | `/cygdrive/c/project` | `C:/project` |
| macOS | `/Users/name/project` | `/Users/name/project` |
| Linux | `/home/user/project` | `/home/user/project` |

## Security Considerations

1. **No Network Access**: All operations are local
2. **No Elevated Privileges**: Runs as current user
3. **Safe File Operations**: Only reads config, writes logs
4. **PowerShell Escaping**: Special characters properly escaped
5. **Path Validation**: Paths validated before use

## Performance Characteristics

| Operation | Typical Duration |
|-----------|------------------|
| Hook trigger to audio start | < 500ms |
| Audio playback | 1-3 seconds |
| Log write | < 10ms |
| Config load | < 50ms |

## Dependencies

### Runtime Dependencies
- Python 3.6+ (all platforms)
- PowerShell 5.1+ (Windows)
- afplay (macOS, built-in)
- mpg123/ffplay/aplay (Linux, may need install)

### No External Python Packages Required
The hook runner uses only Python standard library modules:
- `os`, `sys`, `json`, `subprocess`
- `pathlib`, `platform`, `datetime`
- `shutil`, `tempfile`

---

*For installation instructions, see [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)*
*For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)*
