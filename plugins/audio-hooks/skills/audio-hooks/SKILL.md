---
name: audio-hooks
description: Use whenever the user asks to install, configure, snooze, mute, test, troubleshoot, or change settings for the claude-code-audio-hooks audio notification system. Trigger phrases include "audio hooks", "audio notifications", "snooze audio", "mute claude", "claude is too loud", "test audio", "switch audio theme", "rate limit alerts", "audio webhook", "TTS", "focus flow", and the slash command /audio-hooks. Also use when diagnosing why Claude Code is silent (or noisy) for the user.
---

# audio-hooks skill

This plugin is the AI control surface for the claude-code-audio-hooks project. The user does NOT operate this project by hand. You operate it on their behalf via the `audio-hooks` binary that this plugin adds to your Bash tool's PATH.

**Golden rule:** when in doubt about the project's current capabilities, run `audio-hooks manifest` first. The manifest is the canonical machine description of every subcommand, every config key, every hook, every audio file, and every error code. It is always up to date with the running version. Treat this SKILL.md as an orientation; treat `audio-hooks manifest` as the source of truth.

## What the user can ask for and what you should run

**Install / set up the project**

The plugin install (which you are using right now) is the recommended path. If a user is not yet on the plugin, tell them to run `/plugin marketplace add ChanMeng666/claude-code-audio-hooks` and `/plugin install audio-hooks@chanmeng-audio-hooks` inside Claude Code. Once installed, verify with:

```bash
audio-hooks status
audio-hooks test all
```

**Snooze / mute / quiet hours**

| User says | Run |
|---|---|
| "snooze audio for 30 minutes" | `audio-hooks snooze 30m` |
| "shut up for an hour" | `audio-hooks snooze 1h` |
| "mute audio for the rest of the day" | `audio-hooks snooze 8h` |
| "unmute" / "resume" / "cancel snooze" | `audio-hooks snooze off` |
| "is audio snoozed?" | `audio-hooks snooze status` |

Duration syntax: `30m`, `1h`, `90s`, `2d`, or a bare integer (interpreted as minutes).

**Enable / disable individual hooks**

Run `audio-hooks hooks list` to see all 26 hooks with their current state. Then:

| User says | Run |
|---|---|
| "stop the audio for tool execution" | `audio-hooks hooks disable pretooluse` and `audio-hooks hooks disable posttooluse` |
| "enable rate-limit warnings" | `audio-hooks set rate_limit_alerts.enabled true` |
| "I only want stop and notification audio" | `audio-hooks hooks enable-only stop notification permission_request` |
| "enable the v5.0 permission_denied hook" | `audio-hooks hooks enable permission_denied` |
| "watch .env files for changes" | `audio-hooks hooks enable file_changed` and `audio-hooks set file_changed.watch '[".env",".envrc"]'` |

**Change audio theme**

The project ships two themes. `default` is voice recordings, `custom` is non-voice chimes.

```bash
audio-hooks theme list                  # show available + current
audio-hooks theme set custom            # switch to chimes
audio-hooks theme set default           # switch to voice
```

**Webhook fan-out (Slack / Discord / Teams / ntfy / raw)**

```bash
audio-hooks webhook set --url https://ntfy.sh/my-claude-channel --format ntfy
audio-hooks webhook set --url https://hooks.slack.com/services/... --format slack
audio-hooks webhook test                # POST a test payload
audio-hooks webhook clear               # disable
```

The raw format ships the `audio-hooks.webhook.v1` schema. Every event includes `session_id`, `session_name`, `worktree`, `agent`, `rate_limits`, `last_assistant_message`, `notification_type`, `error_type`, `source`, `trigger`, `load_reason`, and `permission_suggestions` at the top level.

**Text-to-speech**

```bash
audio-hooks tts set --enabled true
# v5.0: TTS Claude's actual final reply on stop/subagent_stop
audio-hooks tts set --speak-assistant-message true
audio-hooks tts set --assistant-message-max-chars 200
```

**Rate-limit alerts (v5.0)**

The runner inspects every hook's stdin for `rate_limits.{five_hour,seven_day}` and plays a one-shot warning when crossing thresholds. Default thresholds are `[80, 95]`. Each (window, threshold, resets_at) tuple fires exactly once per reset window, so the user is alerted at 80% and again at 95% but never spammed.

```bash
audio-hooks rate-limits set --enabled true
audio-hooks rate-limits set --five-hour-thresholds 75,90,98
audio-hooks rate-limits set --seven-day-thresholds 80,95
```

**Test that audio is actually working**

```bash
audio-hooks test all                    # exercise every enabled hook
audio-hooks test stop                   # one specific hook
audio-hooks test session_start_resume   # a v5.0 matcher variant
```

**Troubleshooting "no sound" / "wrong sound"**

Always run `audio-hooks diagnose` first. It returns a JSON document listing the platform, audio player binary, the state of `~/.claude/settings.json` (including `disableAllHooks`), and any audio files missing for the active theme. Errors come with stable `code` enums and a `suggested_command` you should run.

Common error codes you may see:

| Code | What it means | Run |
|---|---|---|
| `SETTINGS_DISABLE_ALL_HOOKS` | The user (or their managed settings) has set `disableAllHooks: true` | Tell the user; Claude Code's config takes precedence |
| `AUDIO_PLAYER_NOT_FOUND` | No mpg123/ffplay/aplay on Linux, or PowerShell missing on Windows | `sudo apt install mpg123` (Linux) |
| `AUDIO_FILE_MISSING` | Audio files for the active theme are missing | `audio-hooks theme set default` to fall back |
| `WEBHOOK_HTTP_ERROR` / `WEBHOOK_TIMEOUT` | Webhook unreachable | `audio-hooks webhook test` and inspect the URL |

After running any fix, verify with `audio-hooks logs tail --n 20` to see the recent NDJSON event stream.

## Reading the logs

All log events are NDJSON (one JSON object per line) under `${CLAUDE_PLUGIN_DATA}/logs/events.ndjson`. Schema is `audio-hooks.v1`. Each event has `ts`, `level`, `hook`, `session_id`, `action`, and event-specific fields. Errors include `error.code`, `error.hint`, and `error.suggested_command`.

```bash
audio-hooks logs tail --n 50              # last 50 events
audio-hooks logs tail --n 100 --level error
audio-hooks logs clear
```

## Reading the manifest (canonical introspection)

`audio-hooks manifest` returns a single JSON document with:

- `subcommands` — every CLI subcommand with arg list and description
- `hooks` — every hook with default state, audio file, description
- `config_keys` — every dotted config path
- `themes` — available audio themes
- `error_codes` — every stable error code with hint and suggested_command
- `env_vars` — every recognised environment variable
- `log_schema` and `webhook_schema` version strings

`audio-hooks manifest --schema` returns the JSON Schema for `user_preferences.json` (use this when you need to validate or generate config).

If any user request feels like it might involve a project capability you don't immediately recognise, **read the manifest first** instead of guessing. The manifest never lies; this skill might lag behind it after an update.

## What you should NOT do

- Do NOT edit `user_preferences.json` directly. Use `audio-hooks set` and the typed setters (`hooks enable`, `theme set`, `webhook set`, `tts set`, `rate-limits set`). They round-trip through validation and emit structured success/error JSON.
- Do NOT prompt the user with a [y/N]. Defaults are sensible. If the user gave you a specific instruction, just run the command.
- Do NOT try to install via `bash scripts/install-complete.sh` when the plugin install path is available — the plugin path is the recommended one.
- Do NOT modify the four hook files in `~/.claude/settings.json` by hand. Use `audio-hooks install --plugin` to register/deregister, or rely on `/plugin install` to do it.
- Do NOT translate any of the JSON output. The keys and values are stable interface contracts.

## Quick reference

```bash
audio-hooks manifest                       # canonical introspection — read this first
audio-hooks status                         # full project state snapshot
audio-hooks version                        # version + install detection
audio-hooks diagnose                       # system check + warnings + errors

audio-hooks hooks list                     # all 26 hooks
audio-hooks hooks enable <name>            # turn one on
audio-hooks hooks disable <name>           # turn one off
audio-hooks hooks enable-only <a> <b>      # exclusive enable

audio-hooks snooze [duration|off|status]   # mute (default 30m)
audio-hooks theme set <default|custom>     # switch theme
audio-hooks webhook set --url <u> --format <f>
audio-hooks tts set --enabled true --speak-assistant-message true
audio-hooks rate-limits set --five-hour-thresholds 80,95

audio-hooks test <hook|all>                # play a hook end-to-end
audio-hooks logs tail --n 50               # recent NDJSON events

audio-hooks get <dotted.key>               # any config key
audio-hooks set <dotted.key> <value>       # any config key (auto-coerces)
```
