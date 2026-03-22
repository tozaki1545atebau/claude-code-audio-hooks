# Changelog

All notable changes to Claude Code Audio Hooks will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.6.0] - 2026-03-22

### Added
- **Async hook execution**: All hooks now register with `"async": true` in settings.json — Claude Code fires hooks in the background and never waits for audio playback, eliminating 200-500ms latency per hook invocation
- **Smart matchers**: High-noise hooks now use Claude Code's native regex matchers to reduce notification spam:
  - `PreToolUse` only fires for `Bash` tool (not Read/Glob/Grep)
  - `PostToolUseFailure` only fires for `Bash|Write|Edit` tools
- **User-configurable filters**: New `filters` section in `user_preferences.json` for per-hook regex filtering on stdin JSON fields (e.g., filter by tool_name, error content, agent_type)
- **Richer notification context**: Desktop notifications now show actionable details from stdin JSON:
  - "Bash failed: `npm test` — exit code 1" (instead of "Tool failed: Bash")
  - "Running Bash: `npm install`" (instead of "Running: Bash")
  - "Permission needed: Bash — `rm -rf node_modules`" (instead of "Permission needed: Bash")
- **Notification detail level**: New `notification_settings.detail_level` config option (`minimal`, `standard`, `verbose`)
- **Webhook integration**: Send hook events to external services via HTTP POST:
  - Supported services: Slack, Discord, Microsoft Teams, ntfy.sh, and custom webhook URLs
  - New `webhook_settings` section in config with `url`, `format`, `hook_types`, and `headers`
  - Runs in background thread — never blocks other notifications
  - Uses only Python standard library (urllib.request) — no external dependencies

### Changed
- `hook_runner.py` version bumped to 4.6.0
- All installer scripts (`install-complete.sh`, `install-windows.ps1`, `quick-setup.sh`) now generate async hook registrations
- `get_notification_context()` rewritten with `_truncate()` helper and `_get_tool_detail()` for richer stdin JSON extraction
- `run_hook()` pipeline now includes filter check and webhook step
- Updated all documentation (CLAUDE.md, README.md, CHANGELOG.md, ARCHITECTURE.md)

---

## [4.5.0] - 2026-03-22

### Added
- **8 new hook types** — full coverage of all 22 Claude Code hook events (up from 14):
  - `StopFailure`: Fires when a turn ends due to an API error (rate limit, auth failure, server error)
  - `PostCompact`: Fires after context compaction completes
  - `ConfigChange`: Fires when a configuration file changes during a session
  - `InstructionsLoaded`: Fires when CLAUDE.md or `.claude/rules/*.md` files are loaded into context
  - `WorktreeCreate`: Fires when a worktree is created for isolated tasks
  - `WorktreeRemove`: Fires when a worktree is removed/cleaned up
  - `Elicitation`: Fires when an MCP server requests user input during a tool call
  - `ElicitationResult`: Fires after a user responds to an MCP elicitation
- **16 new audio files** (8 voice + 8 chime) generated via ElevenLabs:
  - Voice (Jessica): stop-failure.mp3, post-compact.mp3, config-change.mp3, instructions-loaded.mp3, worktree-create.mp3, worktree-remove.mp3, elicitation.mp3, elicitation-result.mp3
  - Chime: chime-stop-failure.mp3, chime-post-compact.mp3, chime-config-change.mp3, chime-instructions-loaded.mp3, chime-worktree-create.mp3, chime-worktree-remove.mp3, chime-elicitation.mp3, chime-elicitation-result.mp3
- Context extraction for all 8 new hooks in `get_notification_context()`
- TTS messages for StopFailure, PostCompact, ConfigChange, and Elicitation hooks

### Changed
- `hook_runner.py` version bumped to 4.5.0
- Audio file count per theme: 14 → 22
- Total hook count: 14 → 22
- Updated all installer scripts (`install-complete.sh`, `install-windows.ps1`) with new hook registrations
- Updated `configure.sh` with new hook names, descriptions, and defaults
- Updated `default_preferences.json` and `user_preferences.json` with new hook entries
- Updated `CLAUDE.md` hook tables, mermaid diagrams, and version references
- Updated `README.md` hook count references and added documentation for all 8 new hooks

---

## [4.4.0] - 2026-03-13

### Added
- **Snooze / Temporary Mute** (closes #7): Temporarily silence all audio hooks for a specified duration with automatic resumption
  - New `scripts/snooze.sh` standalone CLI: `bash scripts/snooze.sh 1h` to snooze, `status` to check, `off` to resume
  - Marker-file based design — no daemon or cleanup needed; hooks self-expire
  - Accepts flexible duration formats: `30m`, `1h`, `2h`, `90m`, bare numbers (minutes), `30s`
  - `--snooze`, `--resume`, `--snooze-status` flags added to `scripts/configure.sh`
  - `--snooze`, `--resume`, `--snooze-status` flags added to `scripts/quick-configure.sh` (inline, works via `curl | bash`)
  - Snooze check integrated into both `hooks/hook_runner.py` (Python) and `hooks/shared/hook_config.sh` (Bash)
  - Debug logging: snoozed hooks log "SNOOZED" with remaining time

### Changed
- `hook_runner.py` version bumped to 4.4.0

---

## [4.3.1] - 2026-02-17

### Added
- **`scripts/quick-configure.sh`**: Lightweight hook manager for Quick Setup (Lite tier) users — enable, disable, or list individual hooks without cloning the repository
  - `--list` shows which of the 4 Quick Setup hooks are enabled/disabled
  - `--disable <Hook>` removes a hook from `~/.claude/settings.json`
  - `--enable <Hook>` re-adds a hook with the correct platform-specific command
  - `--only <Hook> [Hook...]` keeps only the specified hooks, removes the rest
  - Works via `curl | bash` (no clone needed), same pattern as `quick-setup.sh`
  - Case-insensitive hook name matching
  - Supports Python and Node.js for JSON manipulation

### Fixed
- **`scripts/quick-unsetup.sh`**: Now removes all 4 installed hooks including `PermissionRequest` (was only removing 3: Stop, Notification, SubagentStop)

---

## [4.3.0] - 2026-02-17

### Added
- **Per-hook notification mode overrides**: New `notification_settings.per_hook` config allows independently controlling audio and desktop notifications per hook type (e.g., `"pretooluse": "audio_only"` to skip desktop notifications for frequent hooks)
- **`disabled` notification mode**: Suppresses both audio and desktop notifications while still allowing TTS and logging — different from `enabled_hooks: false` which skips everything
- **`--hook-mode` CLI flag**: `bash scripts/configure.sh --hook-mode pretooluse=audio_only posttooluse=disabled` for quick per-hook mode configuration
- Per-hook mode validation with automatic fallback to global mode on invalid values

### Changed
- `hook_runner.py` notification mode resolution now checks `per_hook` overrides before falling back to global `notification_settings.mode`
- Debug logging now shows both per-hook and global mode for each hook trigger
- Updated `config/default_preferences.json` and `config/user_preferences.json` with `per_hook` field
- Updated CLAUDE.md, README.md with per-hook notification mode documentation

### Upgrade

No reinstall needed — existing installations self-update automatically on the next hook trigger after `git pull`. The `per_hook` field is fully backward compatible: if absent, all hooks use the global mode as before.

---

## [4.2.2] - 2026-02-14

### Fixed
- **Audio theme switching broken**: The `audio_files` section in config templates hardcoded all 14 hooks to `default/...`, silently overriding the `audio_theme` setting — switching to `"custom"` had no effect
- **`get_audio_file()` logic**: Now ignores `audio_files` entries that match the default template pattern (`default/<filename>`), so `audio_theme` is always respected
- **Stale installed copy**: `~/.claude/hooks/hook_runner.py` was copied once at install and never updated after `git pull`
- **`configure.sh --theme` incomplete**: Only edited JSON config without syncing `hook_runner.py` to `~/.claude/hooks/`

### Added
- **Auto-sync**: `hook_runner.py` now includes `HOOK_RUNNER_VERSION` constant and `check_and_self_update()` — the installed copy in `~/.claude/hooks/` detects newer versions in the project directory and self-updates on next hook trigger
- **configure.sh hook_runner sync**: `--theme` command now copies `hook_runner.py` to `~/.claude/hooks/` after switching theme
- **README "Ask Claude Code" table**: Quick-reference showing users what to say to Claude Code for theme switching, hook toggling, and config checks

### Changed
- Removed `audio_files` block from `config/default_preferences.json` and `config/user_preferences.json` (backward compatible — `get_audio_file()` handles missing section via `config.get("audio_files", {})`)
- Updated README config examples to use `audio_theme` instead of per-hook `audio_files`
- Updated version references to 4.2.2 across CLAUDE.md, README.md

### Upgrade

No reinstall needed — existing installations self-update automatically on the next hook trigger after `git pull`. Or force sync now:
```bash
cd ~/claude-code-audio-hooks
git pull
cp hooks/hook_runner.py ~/.claude/hooks/hook_runner.py
```

---

## [4.2.0] - 2026-02-13

### Added
- **PostToolUseFailure hook**: Audio alert when a tool execution fails (matches on tool name)
- **SubagentStart hook**: Audio alert when a background subagent is spawned (matches on agent type)
- **TeammateIdle hook**: Audio alert when an Agent Teams teammate goes idle
- **TaskCompleted hook**: Audio alert when an Agent Teams task is completed
- 5 new ElevenLabs Jessica voice audio files: `permission-request.mp3`, `tool-failed.mp3`, `subagent-start.mp3`, `teammate-idle.mp3`, `team-task-done.mp3`
- Full coverage of all 14 Claude Code hook events

### Changed
- Total hook types: 10 → 14
- Total audio files: 9 → 14 (each hook now has a unique audio file)
- `permission_request` hook now uses its own `permission-request.mp3` (was sharing `notification-urgent.mp3`)
- `posttoolusefailure` uses critical urgency for desktop notifications
- Updated all documentation to reflect new hook count
- Updated installers to register all 14 hook types with correct matcher support

### Upgrade

Re-run your installer to register the new hooks:
```bash
# Full Install
bash scripts/install-complete.sh      # macOS/Linux/WSL/Git Bash
.\scripts\install-windows.ps1         # Windows PowerShell
```

Note: All 4 new hooks are disabled by default. Enable them in `config/user_preferences.json` if needed.

---

## [4.1.1] - 2026-02-13

### Feature: PermissionRequest Hook Support

Adds `PermissionRequest` hook support — the "Allow this bash command?" permission dialog now triggers audio and desktop notifications. Closes #5.

### Added

- **`PermissionRequest` hook** — 4th default-enabled hook across all installation tiers
  - Quick Setup (macOS): Basso.aiff (distinct from Sosumi for Notification)
  - Quick Setup (Linux): dialog-warning.oga
  - Quick Setup (WSL/Git Bash): SystemSounds.Question
  - Full Install (all platforms): notification-urgent.mp3
- Context extraction for permission_request: shows `Permission needed: <tool_name>`
- Critical urgency desktop notifications for permission_request (same as notification)
- TTS message: "Permission required"

### Changed

- `hooks/hook_runner.py` — Added permission_request to defaults, context extraction, critical urgency
- `scripts/quick-setup.sh` — Added PermissionRequest as 4th hook with distinct system sounds
- `scripts/install-complete.sh` — Registered PermissionRequest with matcher
- `scripts/install-windows.ps1` — Registered PermissionRequest with matcher
- `config/default_preferences.json` / `config/user_preferences.json` — Added permission_request entries
- `CLAUDE.md` — Updated hook diagrams, tables, settings examples
- `README.md` — Updated notification types from 9→10, added PermissionRequest documentation

### Upgrade

Re-run your installer to register the new hook:
```bash
# Quick Setup
curl -sL https://raw.githubusercontent.com/ChanMeng666/claude-code-audio-hooks/master/scripts/quick-setup.sh | bash

# Full Install
bash scripts/install-complete.sh      # macOS/Linux/WSL/Git Bash
.\scripts\install-windows.ps1         # Windows PowerShell
```

---

## [4.1.0] - 2026-02-13

### Fix: macOS Sequoia (15+) Quick Setup No Audio

Quick Setup on macOS 15+ (Sequoia) produced no sound because `osascript` notifications were silently blocked.

### Fixed

- Quick Setup now uses `afplay` for audio playback (works without permissions on all macOS versions)
- `osascript` notification kept as best-effort for desktop popups
- Each hook uses a distinct system sound: Glass (Stop), Sosumi (Notification), Pop (SubagentStop)

---

## [4.0.3] - 2026-02-11

### Bug Fixes: Installer & Uninstaller Correctness

Fixes multiple bugs that prevented correct hook registration on Windows and blocked uninstallation of modern hook_runner.py-based entries.

### Fixed

#### 1. Windows branch in `install-complete.sh` missing defensive wrapping
- **Bug**: Windows branch registered hooks without `|| true` fallback or `timeout`
- **Impact**: A missing `hook_runner.py` would cause Claude Code hook errors instead of silent fallback
- **Fix**: Added `|| true` to command and `timeout: 10` to hook entries, matching the Unix branch

#### 2. `install-windows.ps1` registered all 9 hooks regardless of config
- **Bug**: PowerShell installer ignored `enabled_hooks` preferences and always registered all 9 hooks
- **Impact**: Users heard audio for every tool call (PreToolUse/PostToolUse), making it very noisy
- **Fix**: Reads `user_preferences.json` (or `default_preferences.json`) and only registers enabled hooks
- **Also fixed**: Added `|| true` and `timeout = 10` to all hook commands
- **Also fixed**: Settings.json now written as UTF-8 without BOM (was using `Out-File -Encoding UTF8` which adds BOM on PS 5.x)

#### 3. `uninstall.sh` could not detect or remove hook_runner.py entries
- **Bug**: `HOOK_SCRIPTS` array and Python `hook_scripts` list did not include `hook_runner.py`
- **Bug**: `endswith(script)` matching failed on commands like `py "path/hook_runner.py" stop || true` (command ends with `|| true`, not with the script name)
- **Impact**: Uninstaller left hook entries in `settings.json` and `hook_runner.py`/`.project_path` files on disk
- **Fix**: Added `hook_runner.py` and `.project_path` to removal lists; changed `endswith` to `in` for substring matching

#### 4. `uninstall.sh` temp dir hardcoded to `/tmp/`
- **Bug**: `rm -f /tmp/claude_audio_hooks.lock` fails on Windows (Git Bash) where temp is `$TEMP`
- **Fix**: Uses `${TEMP:-${TMP:-/tmp}}` for cross-platform temp directory

#### 5. `uninstall.sh` `((removed++))` crashes under `set -e`
- **Bug**: `((removed++))` returns exit code 1 when `removed=0`, causing `set -e` to terminate the script
- **Fix**: Changed to `((removed += 1))` which always returns 0

#### 6. `install-complete.sh` verification grep matched wrong pattern
- **Bug**: Test checked for `notification_hook.sh` in settings.json, but modern installs use `hook_runner.py`
- **Fix**: Changed grep pattern to `hook_runner.py`

#### 7. `install-complete.sh` log paths incorrect
- **Bug**: Displayed `/tmp/claude_hooks_log/hook_triggers.log` which is not the actual log path
- **Fix**: Shows platform-appropriate path (`$TEMP/claude_audio_hooks_queue/logs/` on Windows, `/tmp/claude_audio_hooks_queue/logs/` on Unix)

---

## [3.3.5] - 2026-02-04

### 🐛 Bug Fix: UTF-8 BOM Issue on Windows

This release fixes a critical bug that prevented audio from playing on Windows installations.

### Fixed

#### 1. PowerShell UTF-8 BOM Issue (`scripts/install-windows.ps1`)
- **Bug**: PowerShell 5.x's `-Encoding UTF8` writes files with BOM (Byte Order Mark)
- **Impact**: `.project_path` file started with `\xef\xbb\xbf`, causing path resolution failure
- **Fix**: Use `[System.IO.File]::WriteAllText()` with explicit UTF-8 encoding without BOM

#### 2. Defensive BOM Handling (`hooks/hook_runner.py`)
- **Enhancement**: Changed encoding from `utf-8` to `utf-8-sig` when reading `.project_path`
- **Benefit**: Python's `utf-8-sig` codec automatically strips BOM if present
- **Backward Compatible**: Works correctly with both BOM and non-BOM files

### Technical Details

The issue manifested as `NO_AUDIO_CONFIG` in hook trigger logs because:
1. `.project_path` contained `\xef\xbb\xbfD:/path/...` instead of `D:/path/...`
2. Path validation failed since the BOM-prefixed path didn't exist
3. Audio files couldn't be located, resulting in silent failures

---

## [3.3.4] - 2025-12-22

### 🪟 Full Windows Native Support & Cross-Platform Improvements

This release adds comprehensive Windows native support and improves cross-platform compatibility across all environments.

### Added

#### 1. Windows PowerShell Installer (`scripts/install-windows.ps1`)
- **New**: Native PowerShell installer for Windows users who don't use Git Bash
- **Features**:
  - Prerequisite checking (Python 3.6+, Claude Code CLI)
  - Automatic settings.json configuration
  - Installation validation and testing
  - Non-interactive mode (`-NonInteractive` flag)

#### 2. Diagnostic Tool (`scripts/diagnose.py`)
- **New**: Cross-platform diagnostic utility for troubleshooting
- **Checks**:
  - Python version and platform detection (Windows/WSL/macOS/Linux/Git Bash)
  - Hooks directory and hook_runner.py installation status
  - Project path configuration and audio files availability
  - Claude settings.json hook configuration
  - Recent hook trigger logs
- **Options**: `--verbose` for detailed info, `--test-audio` to test playback

#### 3. Debug Logging Mode
- **New**: Set `CLAUDE_HOOKS_DEBUG=1` environment variable to enable detailed logging
- **Logs include**: Hook triggers, path normalization, audio playback attempts, errors
- **Log location**: `$TEMP/claude_audio_hooks_queue/logs/debug.log` (Windows) or `/tmp/claude_audio_hooks_queue/logs/debug.log` (Unix)

### Improved

#### 1. Enhanced `hook_runner.py`
- **Path Normalization**: Handles Git Bash (`/d/...`), WSL2 (`/mnt/c/...`), and Cygwin (`/cygdrive/c/...`) paths
- **PowerShell Safety**: Proper escaping of special characters in audio file paths
- **Temp Directory**: Cross-platform temp directory detection with multiple fallbacks
- **Error Handling**: Granular exception handling with detailed error logging
- **Debug Output**: Comprehensive logging when `CLAUDE_HOOKS_DEBUG=1` is set

#### 2. Improved `install-complete.sh`
- **Temp Directory**: Uses platform-appropriate temp directories (`$TEMP` on Windows, `/tmp` on Unix)
- **Path Format**: Saves `.project_path` in Windows format on Windows environments
- **Python Detection**: Prioritizes `py` launcher on Windows, then `python3`, then `python`

#### 3. Updated `hook_config.sh`
- **Debug Logging**: Added `log_debug()` and `log_error()` functions
- **Temp Directory**: Cross-platform temp directory handling
- **Path Functions**: Unified path conversion with `hook_runner.py`

### Cross-Platform Status
- ✅ **Windows Native**: Full support via PowerShell installer
- ✅ **Windows + Git Bash**: Automatic path conversion
- ✅ **Windows + WSL**: PowerShell audio playback via temp file copy
- ✅ **macOS**: Full support (afplay)
- ✅ **Linux**: Full support (mpg123/ffplay/aplay)
- ✅ **Cygwin**: Full support with path conversion

### Upgrade Instructions

**For existing installations:**
```bash
cd claude-code-audio-hooks
git pull origin master

# Re-run installer to update all components
bash scripts/install-complete.sh  # Linux/macOS/Git Bash
# Or: .\scripts\install-windows.ps1  # Windows PowerShell
```

**To enable debug logging:**
```bash
export CLAUDE_HOOKS_DEBUG=1  # Linux/macOS/Git Bash
# Or: $env:CLAUDE_HOOKS_DEBUG = "1"  # Windows PowerShell
```

---

## [3.3.3] - 2025-11-07

### 🐛 Critical Bug Fixes: WSL Audio & Hooks Format

This release fixes two critical issues affecting WSL users and new installations.

### Fixed

#### 1. WSL Audio Playback Issue
- **Problem**: Windows MediaPlayer could not access audio files via WSL UNC paths (`\\wsl.localhost\...`)
- **Solution**: Audio files are now copied to Windows temp directory (`C:/Windows/Temp`) before playback
- **Impact**: WSL users can now hear audio notifications correctly
- **Technical Details**:
  - Modified `play_audio_internal()` in `hooks/shared/hook_config.sh`
  - Automatic cleanup after playback completes
  - Increased playback wait time from 3s to 4s for reliability
  - Background process handles file cleanup to avoid blocking

#### 2. Hooks Format Compatibility (Credits: @PaddyPatPat)
- **Problem**: Installer generated deprecated hooks format, causing Claude Code v2.0.32+ to report "Invalid Settings"
- **Solution**: Updated installer to generate new array-based format required by Claude Code v2.0.32+
- **Impact**: New installations now work correctly with latest Claude Code
- **Technical Details**:
  - Modified `scripts/install-complete.sh` Python script
  - Old format: `"Notification": "~/.claude/hooks/notification_hook.sh"`
  - New format: `"Notification": [{"hooks": [{"type": "command", "command": "~/.claude/hooks/notification_hook.sh"}]}]`
  - Each hook now formatted as array of matcher objects

### Cross-Platform Status
- ✅ **WSL users**: Both audio playback and hooks format fixed
- ✅ **macOS users**: No changes (continues using afplay)
- ✅ **Linux users**: No changes (continues using mpg123/aplay)
- ✅ **Git Bash users**: No changes (already working)

### Upgrade Instructions

**For existing installations:**
```bash
cd claude-code-audio-hooks
git pull origin master

# Update hook audio playback
cp hooks/shared/hook_config.sh ~/.claude/hooks/shared/hook_config.sh

# Re-run installer to update hooks format
bash scripts/install-complete.sh
```

### Credits
- WSL audio fix: Main development team
- Hooks format fix: Special thanks to [@PaddyPatPat](https://github.com/PaddyPatPat) for identifying and documenting the hooks format issue in [PR #2](https://github.com/ChanMeng666/claude-code-audio-hooks/pull/2)

## [3.3.2] - 2025-11-07

### Note
This version was superseded by v3.3.3 which includes additional hooks format fix. Please upgrade to v3.3.3.

## [3.3.1] - 2025-11-06

### 🐛 Critical Bug Fixes: Installation Script Stability

Fixed critical issues preventing successful installation on WSL and other platforms.

### Fixed
- **Bash arithmetic expression error with `set -e`**:
  - Replaced post-increment operators (`++`) with compound assignment (`+=1`)
  - Post-increment returns 0 when variable is 0, causing `set -e` to exit
  - Affected counters: `STEPS_COMPLETED`, `WARNINGS`, `ERRORS`, and all test counters
  - Installation now completes successfully on all platforms

- **Python type error in configuration validation**:
  - Fixed `TypeError: unsupported operand type(s) for +: 'int' and 'str'`
  - Configuration validation now filters out comment keys (starting with `_`)
  - Properly handles JSON files with inline comments

### Impact
- ✅ **Installation now works reliably on WSL**
- ✅ **All arithmetic operations safe with `set -e`**
- ✅ **Configuration validation handles commented JSON**
- ✅ **No breaking changes** - fully backward compatible

### Technical Details
```bash
# Before (fails with set -e when var=0)
((STEPS_COMPLETED++))

# After (works correctly)
((STEPS_COMPLETED+=1))
```

## [3.3.0] - 2025-11-06

### 🤖 Full Automation Support: Non-Interactive Mode for All Scripts

All core scripts (`install-complete.sh`, `uninstall.sh`, `configure.sh`) now support **non-interactive mode** - enabling complete automation by Claude Code and scripts!

### Added
- **Non-interactive mode for `install-complete.sh`**:
  - `--yes`/`-y`/`--non-interactive` - Skip audio test prompt
  - `--help` - Show comprehensive usage guide
  - Auto-completes installation without user input

- **Non-interactive mode for `uninstall.sh`**:
  - `--yes`/`-y`/`--non-interactive` - Auto-confirm all removals
  - `--help` - Show comprehensive usage guide
  - Automatically removes: hooks, settings, config, audio files
  - Creates backups before deletion
  - Zero prompts, full automation

### Changed
- **Version updates**:
  - `install-complete.sh` → v3.2.0
  - `uninstall.sh` → v3.2
  - Added version info in script headers

### Enhanced
- **Complete Claude Code Automation** - AI assistants can now:
  - Install without prompts: `bash install-complete.sh --yes`
  - Uninstall without prompts: `bash uninstall.sh --yes`
  - Configure hooks: `bash configure.sh --enable notification`
  - Fully automate entire lifecycle

- **CI/CD Ready**:
  - Perfect for deployment pipelines
  - Scriptable setup and teardown
  - No TTY required

### Impact
- ✅ **100% non-interactive capability** across all scripts
- ✅ **Claude Code can fully automate** install/uninstall/configure
- ✅ **Zero user input required** for automation
- ✅ **Backward compatible** - interactive mode still default

### Examples
```bash
# Full automated installation
bash scripts/install-complete.sh --yes

# Full automated uninstallation
bash scripts/uninstall.sh --yes

# Configure hooks programmatically
bash scripts/configure.sh --enable notification stop --disable pretooluse
```

## [3.2.0] - 2025-11-06

### 🤖 Major Enhancement: Dual-Mode Configuration Tool

`configure.sh` now supports **both human-friendly interactive mode AND programmatic CLI interface** - making it usable by Claude Code, scripts, and automation tools!

### Added
- **Programmatic CLI Interface** for `configure.sh`:
  - `--list` - List all hooks and their status
  - `--get <hook>` - Get status of specific hook (returns `true`/`false`)
  - `--enable <hook> [hook2...]` - Enable one or more hooks
  - `--disable <hook> [hook2...]` - Disable one or more hooks
  - `--set <hook>=<value>` - Set hook to specific value
  - `--reset` - Reset to recommended defaults
  - `--help` - Show comprehensive usage guide
- **Batch Operations** - Enable/disable multiple hooks in one command
- **Idempotent Operations** - Safe to run multiple times, only changes what's needed
- **Clear Output** - Visual indicators (✓/✗) for all operations

### Changed
- **configure.sh** is now a **dual-mode tool**:
  - No arguments → Interactive menu (existing functionality preserved)
  - With arguments → Programmatic CLI (new functionality)
- All programmatic commands automatically save changes
- Error handling for unknown hooks (warnings, not failures)

### Enhanced
- **AI Assistant Integration** - Claude Code and other AI tools can now:
  - Query hook configuration programmatically
  - Enable/disable hooks based on user preferences
  - Automate configuration setup
- **Script Automation** - Easy to integrate into deployment scripts
- **Backward Compatible** - Interactive mode works exactly as before

### Impact
- ✅ **Claude Code can now configure hooks!**
- ✅ **Scriptable configuration** - No more manual editing needed
- ✅ **Batch operations** - Change multiple hooks at once
- ✅ **100% backward compatible** - Existing users unaffected

### Examples
```bash
# Check if notification hook is enabled
bash scripts/configure.sh --get notification

# Enable multiple hooks at once
bash scripts/configure.sh --enable notification stop subagent_stop

# Mixed operations in one command
bash scripts/configure.sh --enable notification --disable pretooluse
```

## [3.1.1] - 2025-11-06

### 🧹 Deep Cleanup: Removing All Redundant Scripts

Further simplification by removing truly unnecessary internal scripts and fixing broken references. Now only essential, actively-used files remain.

### Removed
- **`scripts/internal/detect-environment.sh`** (25KB) - Completely redundant
  - Environment detection already integrated in `hooks/shared/path_utils.sh`
  - Never actually called - only mentioned in log messages
  - Removed entire `/scripts/internal/` directory (now empty)
- **`scripts/.internal-tests/check-setup.sh`** (8.3KB) - Unused diagnostic script
  - Not called by install-complete.sh
  - Had broken path references in test-audio.sh
- **`scripts/.internal-tests/test-path-conversion.sh`** (5.7KB) - Never invoked
  - No script in the entire project calls it
  - Pure legacy code

### Fixed
- **Broken references in `test-audio.sh`**:
  - Removed reference to non-existent `./scripts/check-setup.sh`
  - Removed reference to non-existent `docs/AUDIO_CREATION.md`
  - Updated to point users to installer and README.md
- **Misleading suggestions in `install-complete.sh`**:
  - Removed suggestions to manually run `detect-environment.sh`
  - Replaced with advice to re-run installer

### Changed
- **`scripts/.internal-tests/` now contains only 1 file**:
  - `test-path-utils.sh` (8.7KB) - The ONLY test script actually used by installer
  - Everything else eliminated

### Impact
- ✅ **~39KB of truly redundant code removed** (detect-environment.sh + unused tests)
- ✅ **Zero broken references** - All documentation now accurate
- ✅ **Ultra-minimal structure** - Only files that are actually used
- ✅ **No duplicate functionality** - Environment detection in one place only

## [3.1.0] - 2025-11-06

### 🎯 Project Cleanup: Achieving True Single-Installation Simplicity

This release further streamlines the project structure by removing unnecessary files and hiding internal utilities from users. The goal: users clone and run ONE installation command, with ZERO confusion.

### Removed
- **Deleted `/examples/` directory** - Redundant with `/config/` directory
  - Removed outdated v1.0 example files
  - Eliminated duplicate configuration examples
  - Configuration examples now only in `/config/`
- **Deleted `/docs/` directory** - Empty directory, all docs consolidated in README.md
- **Deleted obsolete patch script** - `scripts/internal/apply-windows-fix.sh`
  - v2.x legacy patch script no longer needed
  - All fixes now integrated into `install-complete.sh`
- **Removed personal development files** - Added `.claude/` to `.gitignore`

### Changed
- **Hidden internal test scripts** - Renamed `/scripts/tests/` → `/scripts/.internal-tests/`
  - Test scripts are auto-run by installer, users shouldn't see them
  - Reduces decision paralysis and confusion
  - Updated all internal references to new path
- **Simplified documentation references**
  - Removed suggestions to manually run internal scripts
  - Updated bug report template to request log files instead
  - Simplified project structure diagram
- **Cleaner visible file structure**
  - From 7 top-level directories → 5 directories
  - From 21+ visible files → ~15 essential files
  - Only user-facing scripts visible in `/scripts/`

### Impact
- ✅ **Zero decision anxiety** - One clear installation path
- ✅ **Reduced confusion** - No unnecessary files or scripts visible
- ✅ **Cleaner project** - ~4,100 lines of redundant code removed
- ✅ **Better UX** - Users focus on: Clone → Install → Use

## [3.0.1] - 2025-11-06

### Fixed
- **Uninstall Script**: Fixed bash syntax error on line 115 where `local` keyword was incorrectly used outside function scope

## [3.0.0] - 2025-11-06

### 🎯 Major Release: Streamlined Installation & Zero-Redundancy Project Structure

This release focuses on simplifying the user experience by consolidating all installation, validation, and testing into a single streamlined workflow. Users no longer need to run multiple scripts or worry about patches and upgrades.

### Added
- **Integrated Installation Workflow**: `install-complete.sh` now automatically:
  - Detects environment (WSL, Git Bash, Cygwin, macOS, Linux)
  - Applies platform-specific fixes automatically
  - Validates installation with comprehensive tests
  - Offers optional audio testing at the end
  - All in one smooth, automated process
- **Organized Directory Structure**:
  - `scripts/internal/` - Internal tools auto-run by installer (users don't need to know about these)
  - `scripts/tests/` - Testing tools auto-run by installer (users don't need to run manually)
- **Interactive Audio Testing**: Installer now asks if users want to test audio playback
- **Comprehensive Validation**: Automated 5-point validation during installation

### Changed
- **Simplified Installation**: From 6 manual steps down to 1 command
  - Before v3.0: Clone → Install → Verify → Test → Configure → Restart
  - v3.0: Clone → Install (everything else automatic) → Restart
- **Success Rate Improvement**: From 95% to 98%+ due to integrated diagnostics
- **Installation Time**: Reduced from 2-5 minutes to 1-2 minutes
- **Upgrade Method**: Now recommends uninstall + fresh install instead of upgrade scripts
  - Simpler, cleaner, no conflicts with old structure
  - Takes only 1-2 minutes
  - Guarantees optimal configuration

### Removed (Streamlining)
- **Redundant Scripts**:
  - ❌ `install.sh` - Replaced by enhanced `install-complete.sh`
  - ❌ `upgrade.sh` - Users should uninstall + reinstall for v3.0
  - ❌ Manual `check-setup.sh` runs - Now auto-runs during installation
  - ❌ Manual `detect-environment.sh` runs - Now integrated into installer
  - ❌ Manual path testing - Now automatic during installation
- **Redundant Documentation**:
  - Removed scattered .md files (AI_INSTALL.md, UTILITIES_README.md, etc.)
  - Everything now in README.md only
  - Cleaner, more maintainable documentation

### Relocated (Better Organization)
- `scripts/detect-environment.sh` → `scripts/internal/detect-environment.sh`
- `scripts/apply-windows-fix.sh` → `scripts/internal/apply-windows-fix.sh`
- `scripts/check-setup.sh` → `scripts/tests/check-setup.sh`
- `scripts/test-path-utils.sh` → `scripts/tests/test-path-utils.sh`
- `scripts/test-path-conversion.sh` → `scripts/tests/test-path-conversion.sh`

### Enhanced
- **install-complete.sh v3.0** (was v2.1):
  - Integrated environment detection
  - Automatic platform-specific fixes
  - Comprehensive validation (7 checks)
  - Interactive audio testing option
  - Better error reporting and troubleshooting guidance
- **README.md**:
  - Updated to v3.0 with accurate script references
  - Simplified installation instructions
  - Removed references to deleted scripts
  - Updated troubleshooting section
  - Clearer upgrade instructions
  - Accurate project structure diagram

### User Benefits
- ✅ **One-Command Installation**: Everything handled automatically
- ✅ **No Manual Testing Required**: Installer validates everything
- ✅ **No Patches Needed**: All fixes applied automatically
- ✅ **Cleaner Project**: Only essential user-facing scripts remain
- ✅ **Better Documentation**: Single source of truth (README.md)
- ✅ **Faster Installation**: 1-2 minutes vs 2-5 minutes
- ✅ **Higher Success Rate**: 98%+ vs 95%

### Breaking Changes
- **Directory structure changed**: Old scripts moved to `internal/` and `tests/`
- **Removed scripts**: Users upgrading from v2.x should uninstall first, then install v3.0
- **No upgrade.sh**: Fresh install recommended for cleanest experience

### Migration Guide
For users upgrading from v2.x or earlier:
```bash
cd ~/claude-code-audio-hooks
bash scripts/uninstall.sh  # Remove old version
git pull origin master      # Get v3.0
bash scripts/install-complete.sh  # Fresh install
```

### Technical Details
- Version: 3.0.0
- Scripts reorganized: 11 scripts → 4 user-facing + 5 internal/test scripts
- Installation steps: 11 automated steps (up from 10)
- Total lines of code: Reduced by removing redundancy
- Success rate: 98%+
- Installation time: 1-2 minutes

---

## [2.4.0] - 2025-11-06

### Added
- **Dual Audio System**: Complete flexibility to choose between voice and non-voice notifications
  - 9 new modern UI chime sound effects in `audio/custom/` directory
  - 9 refreshed voice notifications in `audio/default/` directory (Jessica voice from ElevenLabs)
- **Pre-configured Examples**:
  - `config/example_preferences_chimes.json` - All chimes configuration
  - `config/example_preferences_mixed.json` - Mixed voice and chimes with scenario templates
- **Audio Customization Documentation**: New comprehensive section in README explaining:
  - Three audio options (voice-only, chimes-only, mixed)
  - Quick-start guide for switching to chimes
  - Available audio files comparison table
  - Configuration scenarios for different use cases
- **User Choice Philosophy**: System now supports complete user customization
  - Default configuration uses voice (existing behavior preserved)
  - Users can easily switch to chimes or create mixed configurations
  - Simple one-file configuration change to switch audio sets

### Changed
- README.md updated with new "Audio Customization Options" section
- Version badges updated to v2.4.0
- Table of Contents updated with new audio customization section

### Enhanced
- User flexibility: Users can now choose audio style based on personal preference
- Music-friendly option: Chimes don't interfere with background music
- Mixed configurations: Different audio types for different notification priorities

### Background
This release addresses user feedback requesting non-voice notification options, particularly for users who:
- Play music while coding
- Prefer instrumental sounds over AI voices
- Want different audio styles for different notification types

The dual audio system maintains backward compatibility (default voice notifications) while providing complete flexibility for users who want alternatives.

## [2.3.1] - 2025-11-06

### Fixed
- Critical bug in configure.sh save_configuration() function that prevented saving on macOS
- Python heredoc in configure.sh now correctly passes CONFIG_FILE path using shell variable substitution
- Resolved IndexError when accessing sys.argv[1] in Python heredoc

## [2.3.0] - 2025-11-06

### Added
- Full compatibility with macOS default bash 3.2
- Bash version detection in install.sh with helpful warnings
- Compatibility notes in scripts for macOS users

### Fixed
- Replaced bash 4+ associative arrays with indexed arrays in configure.sh and test-audio.sh
- Replaced bash 4+ case conversion operators (${var^^} and ${var,,}) with tr commands in path_utils.sh
- All scripts now work with bash 3.2+ without requiring Homebrew bash on macOS

### Changed
- Refactored configure.sh to use parallel indexed arrays instead of associative arrays
- Refactored test-audio.sh to use parallel indexed arrays for configuration data
- Updated path_utils.sh to use portable tr command for case conversion
- Enhanced README with macOS compatibility information

## [2.2.0] - Previous Release

### Added
- Automatic format compatibility for Claude Code v2.0.32+
- Git Bash path conversion fixes
- Enhanced Windows compatibility

### Fixed
- Path conversion issues on Git Bash
- Audio playback on various Windows environments

## [2.1.0] - Previous Release

### Added
- Hook trigger logging system
- Diagnostic tools for troubleshooting
- View-hook-log.sh script for monitoring hook triggers

## [2.0.0] - Major Release

### Added
- 9 different hook types (up from 1 in v1.0)
- Professional ElevenLabs audio files
- Interactive configuration tool
- JSON-based user preferences
- Audio queue system
- Debounce system
- Automatic v1.0 upgrade support

### Changed
- Complete project restructure
- Modular hook system with shared library
- Cross-platform support improvements

## [1.0.0] - Initial Release

### Added
- Basic stop hook with audio notification
- Simple installation script
- Custom audio support