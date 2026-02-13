# Installation Guide

> **Version:** 4.2.0 | **Last Updated:** 2026-02-13

Complete installation guide for all platforms and environments.

## Prerequisites Check

Before installing, verify you have the required tools:

```mermaid
flowchart TD
    START([Start Installation]) --> CHECK_CLAUDE{Claude Code installed?}

    CHECK_CLAUDE -->|No| INSTALL_CLAUDE[Install Claude Code first]
    INSTALL_CLAUDE --> CHECK_CLAUDE
    CHECK_CLAUDE -->|Yes| CHECK_PYTHON{Python 3.6+ installed?}

    CHECK_PYTHON -->|No| INSTALL_PYTHON[Install Python]
    INSTALL_PYTHON --> CHECK_PYTHON
    CHECK_PYTHON -->|Yes| CHECK_GIT{Git installed?}

    CHECK_GIT -->|No| INSTALL_GIT[Install Git]
    INSTALL_GIT --> CHECK_GIT
    CHECK_GIT -->|Yes| READY([Ready to Install])
```

### Verification Commands

```bash
# Check Claude Code
claude --version
# Expected: claude X.X.X

# Check Python (try all variants)
python3 --version   # Linux/macOS
python --version    # May work
py --version        # Windows Python Launcher

# Check Git
git --version
```

### Installing Missing Prerequisites

| Tool | Windows | macOS | Linux |
|------|---------|-------|-------|
| Claude Code | [Download](https://docs.anthropic.com/claude/docs/claude-code) | [Download](https://docs.anthropic.com/claude/docs/claude-code) | [Download](https://docs.anthropic.com/claude/docs/claude-code) |
| Python | [python.org](https://www.python.org/downloads/) | `brew install python3` | `sudo apt install python3` |
| Git | [git-scm.com](https://git-scm.com/) | `brew install git` | `sudo apt install git` |

---

## Platform Selection Guide

```mermaid
flowchart TD
    Q1{What operating system?}

    Q1 -->|Windows| Q2{Which terminal?}
    Q1 -->|macOS| MAC[macOS Installation]
    Q1 -->|Linux| LINUX[Linux Installation]

    Q2 -->|PowerShell or CMD| WIN_PS[Windows PowerShell Installation]
    Q2 -->|Git Bash| WIN_GB[Git Bash Installation]
    Q2 -->|WSL Ubuntu/Debian| WSL[WSL Installation]
    Q2 -->|Cygwin| CYG[Cygwin Installation]

    click WIN_PS "#windows-powershell-installation"
    click WIN_GB "#windows-git-bash-installation"
    click WSL "#wsl-installation"
    click MAC "#macos-installation"
    click LINUX "#linux-installation"
```

---

## Windows PowerShell Installation

**Best for:** Windows users who don't use Git Bash

### Step 1: Clone Repository

```powershell
# Navigate to desired location
cd $HOME\Documents

# Clone repository
git clone https://github.com/ChanMeng666/claude-code-audio-hooks.git
cd claude-code-audio-hooks
```

### Step 2: Run PowerShell Installer

```powershell
# Run installer
.\scripts\install-windows.ps1

# Or for non-interactive mode
.\scripts\install-windows.ps1 -NonInteractive
```

### Step 3: Verify Installation

```powershell
# Check hook runner installed
Test-Path "$env:USERPROFILE\.claude\hooks\hook_runner.py"
# Should return: True

# Check settings configured
Get-Content "$env:USERPROFILE\.claude\settings.json" | Select-String "hook_runner"
# Should show hook configurations
```

### Step 4: Restart and Test

```powershell
# Close and reopen PowerShell, then:
claude "What is 2+2?"
# Listen for audio when response completes
```

---

## Windows Git Bash Installation

**Best for:** Windows users with Git Bash installed

### Step 1: Clone Repository

```bash
# Navigate to desired location
cd ~/Documents

# Clone repository
git clone https://github.com/ChanMeng666/claude-code-audio-hooks.git
cd claude-code-audio-hooks
```

### Step 2: Run Bash Installer

```bash
# Run installer
bash scripts/install-complete.sh

# Or for non-interactive mode
bash scripts/install-complete.sh --yes
```

### Step 3: Verify Installation

```bash
# Check hook runner installed
ls -la ~/.claude/hooks/hook_runner.py

# Check project path (should be Windows format)
cat ~/.claude/hooks/.project_path
# Should show: D:/path/to/claude-code-audio-hooks
```

### Step 4: Restart and Test

```bash
# Close and reopen Git Bash, then:
claude "What is 2+2?"
```

---

## WSL Installation

**Best for:** Windows users who prefer Linux environment

```mermaid
sequenceDiagram
    participant User
    participant WSL
    participant Windows
    participant Audio

    User->>WSL: Run installer
    WSL->>WSL: Install hooks
    WSL->>Windows: Store path in Windows format
    User->>WSL: Trigger Claude Code
    WSL->>Windows: Call PowerShell
    Windows->>Audio: Play via MediaPlayer
```

### Step 1: Clone Repository

```bash
# In WSL terminal
cd ~

# Clone repository
git clone https://github.com/ChanMeng666/claude-code-audio-hooks.git
cd claude-code-audio-hooks
```

### Step 2: Run Installer

```bash
bash scripts/install-complete.sh
```

### Step 3: Verify PowerShell Access

```bash
# Test PowerShell is accessible from WSL
powershell.exe -Command "Write-Host 'PowerShell works'"
# Should output: PowerShell works
```

### Step 4: Test Audio

```bash
# Test audio playback
python scripts/diagnose.py --test-audio
```

### WSL-Specific Notes

- Audio plays through Windows, not WSL
- Audio files are automatically copied to Windows temp directory
- PowerShell must be accessible from WSL path

---

## macOS Installation

**Best for:** All macOS users

### Step 1: Clone Repository

```bash
cd ~

git clone https://github.com/ChanMeng666/claude-code-audio-hooks.git
cd claude-code-audio-hooks
```

### Step 2: Run Installer

```bash
bash scripts/install-complete.sh
```

### Step 3: Verify Installation

```bash
# Check hook runner
ls -la ~/.claude/hooks/hook_runner.py

# Check afplay (built-in audio player)
which afplay
# Should show: /usr/bin/afplay
```

### Step 4: Test

```bash
# Restart terminal, then:
claude "What is 2+2?"
```

---

## Linux Installation

**Best for:** Linux desktop users

### Step 1: Install Audio Player

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install mpg123

# Fedora
sudo dnf install mpg123

# Arch Linux
sudo pacman -S mpg123

# Verify installation
mpg123 --version
```

### Step 2: Clone Repository

```bash
cd ~

git clone https://github.com/ChanMeng666/claude-code-audio-hooks.git
cd claude-code-audio-hooks
```

### Step 3: Run Installer

```bash
bash scripts/install-complete.sh
```

### Step 4: Test Audio

```bash
# Test audio directly
mpg123 ~/claude-code-audio-hooks/audio/default/task-complete.mp3

# Or use diagnostic tool
python scripts/diagnose.py --test-audio
```

---

## Post-Installation Configuration

### Configure Enabled Hooks

After installation, you can customize which hooks trigger audio:

```bash
# Interactive configuration
bash scripts/configure.sh

# Or edit directly
nano ~/claude-code-audio-hooks/config/user_preferences.json
```

### Recommended Configuration

```json
{
  "enabled_hooks": {
    "notification": true,         // KEEP: Important alerts
    "stop": true,                 // KEEP: Task completion
    "subagent_stop": true,        // KEEP: Background tasks
    "permission_request": true,   // KEEP: Permission dialogs
    "session_start": false,       // Optional
    "session_end": false,         // Optional
    "pretooluse": false,          // DISABLE: Too noisy
    "posttooluse": false,         // DISABLE: Too noisy
    "posttoolusefailure": false,  // Optional: Tool failures
    "userpromptsubmit": false,
    "precompact": false,
    "subagent_start": false,      // Optional: Subagent spawned
    "teammate_idle": false,       // Optional: Agent Teams
    "task_completed": false       // Optional: Agent Teams
  }
}
```

### Enable Debug Logging

For troubleshooting, enable debug mode:

```bash
# Bash/Zsh (add to ~/.bashrc or ~/.zshrc for persistence)
export CLAUDE_HOOKS_DEBUG=1

# PowerShell (add to $PROFILE for persistence)
$env:CLAUDE_HOOKS_DEBUG = "1"
```

---

## Installation Verification

### Quick Verification

```mermaid
flowchart LR
    A[Run Diagnostic] --> B{All checks pass?}
    B -->|Yes| C[Installation Complete]
    B -->|No| D[See Troubleshooting]
```

```bash
# Run full diagnostic
python scripts/diagnose.py -v --test-audio
```

### Manual Verification Checklist

| Check | Command | Expected |
|-------|---------|----------|
| Hook runner exists | `ls ~/.claude/hooks/hook_runner.py` | File exists |
| Project path saved | `cat ~/.claude/hooks/.project_path` | Valid path |
| Settings configured | `grep hook_runner ~/.claude/settings.json` | Hook entries found |
| User preferences | `cat config/user_preferences.json` | JSON with enabled_hooks |
| Audio files | `ls audio/default/*.mp3 \| wc -l` | 14 files |

---

## Upgrading from Previous Versions

### From v3.x

```bash
cd claude-code-audio-hooks
git pull origin master
bash scripts/install-complete.sh
```

### From v2.x or v1.x

```bash
# Uninstall old version first
bash scripts/uninstall.sh

# Get latest code
git pull origin master

# Fresh install
bash scripts/install-complete.sh
```

---

## Uninstallation

```bash
# Interactive uninstall
bash scripts/uninstall.sh

# Non-interactive uninstall
bash scripts/uninstall.sh --yes
```

This removes:
- Hook configurations from `~/.claude/settings.json`
- Hook scripts from `~/.claude/hooks/`
- Keeps project directory and audio files

---

## Next Steps

1. **Customize audio files**: Replace MP3 files in `audio/default/`
2. **Configure hooks**: Run `bash scripts/configure.sh`
3. **Enable debug logging**: Set `CLAUDE_HOOKS_DEBUG=1`
4. **Report issues**: [GitHub Issues](https://github.com/ChanMeng666/claude-code-audio-hooks/issues)

---

*For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)*
*For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md)*
