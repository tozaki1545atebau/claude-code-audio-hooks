# Claude Code Audio Hooks — AI Operator Guide

> **Version:** 5.0.3 | **Last Updated:** 2026-04-11

This document is the canonical machine-facing guide for the claude-code-audio-hooks project. It is written for **Claude Code (and other AI agents) as the operator** — not for humans. A human user says "install audio hooks for me" or "snooze audio for an hour" and you do everything via the project's structured CLI without any human-in-the-loop confirmation, menu navigation, or log file reading.

## Operating principles

1. **`audio-hooks` is the only interface you need.** It is a single Python binary on your Bash tool's PATH (when installed as a plugin) that exposes every operation as a JSON-output subcommand. No prompts. No colors. No spinners. Always returns valid JSON to stdout. Errors carry stable `code` enums and a `suggested_command` you can run next.
2. **`audio-hooks manifest` is the source of truth.** This document is an orientation; the manifest is the live, authoritative description of every subcommand, every config key, every hook, every audio file, every error code, and every environment variable. Read the manifest at the start of any non-trivial task instead of guessing.
3. **Logs are NDJSON.** One JSON object per line at `${CLAUDE_PLUGIN_DATA}/logs/events.ndjson` (plugin install) or under the project temp dir (script install). Schema is `audio-hooks.v1`. Read with `audio-hooks logs tail`.
4. **No interactive scripts.** Every shell script in `scripts/` is non-interactive when stdin is not a TTY or `CLAUDE_NONINTERACTIVE=1` is set. Human-only menus (`configure.sh`, `test-audio.sh`) auto-redirect to `audio-hooks` via structured JSON pointers.
5. **You never edit `user_preferences.json` by hand.** Use `audio-hooks set` and the typed setters.

## Personal notes (my fork)

> I keep `volume` defaulted to `0.4` instead of the upstream `0.7` — less jarring when working late.
> To apply after install: `audio-hooks set volume 0.4`
>
> I also disable the notification sound on tool_use events — I find it too noisy during long agentic runs.
> To apply after install: `audio-hooks set hooks.tool_use.enabled false`
>
> I disable the stop/completion sound as well — I usually have notifications for that via the OS already.
> To apply after install: `audio-hooks set hooks.stop.enabled false`

## AI quickstart for Claude Code operating this project on a human's behalf

When the user says *"install audio-hooks for me"*, **you (Claude Code) run these via your Bash tool**, then ask the user to type `/reload-plugins` once:

```bash
# Step 1: marketplace add (you run this via Bash tool)
claude plugin marketplace add ChanMeng666/claude-code-audio-hooks

# Step 2: plugin install (you run this via Bash tool)
claude plugin install audio-hooks@chanmeng-audio-hooks

# Step 3: tell the user to type /reload-plugins  
# (you cannot run this — it is a REPL slash command with no CLI equivalent)
```

Then the user types `/reload-plugins` themselves. After that, **you can run every other operation via the Bash tool forever** — `audio-hooks status`, `audio-hooks diagnose`, `audio-hooks test all`, `audio-hooks theme set custom`, etc.

```bash
# Ste
```
