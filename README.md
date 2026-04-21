<div align="center"><a name="readme-top"></a>

[![Project Banner](./public/claude-code-audio-hooks-logo.svg)](#)

# Claude Code Audio Hooks

**AI-operated audio notification system for Claude Code.**<br/>
You type one slash command at install time. Then natural language forever.<br/>
26 hook events, 2 audio themes, rate-limit alerts, webhooks, TTS, context monitor — all operated by Claude Code on your behalf.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-5.0.3-blue.svg)](https://github.com/ChanMeng666/claude-code-audio-hooks)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-green.svg)](https://github.com/ChanMeng666/claude-code-audio-hooks)
[![Claude Code](https://img.shields.io/badge/Claude_Code-v2.1.80%2B-brightgreen.svg)](https://claude.ai/download)
[![Plugin](https://img.shields.io/badge/install-just_talk_to_Claude-purple.svg)](#-install-in-60-seconds)

**Share This Project**

[![][share-x-shield]][share-x-link]
[![][share-linkedin-shield]][share-linkedin-link]
[![][share-reddit-shield]][share-reddit-link]
[![][share-telegram-shield]][share-telegram-link]
[![][share-whatsapp-shield]][share-whatsapp-link]

---

### Promotional Video

https://github.com/user-attachments/assets/3504d214-efac-4e01-84c0-426430b842d6

<sup>Built with Remotion, Claude Code, ElevenLabs & Suno. Source: <a href="https://github.com/ChanMeng666/claude-code-audio-hooks-promo-video">claude-code-audio-hooks-promo-video</a></sup>

> **Personal fork note:** I'm using this primarily on macOS with the `minimal` audio theme. If you're on macOS and find the default notification sounds too loud during focus sessions, check the [Troubleshooting](#-troubleshooting) section for volume configuration tips.
>
> **Additional personal note:** I've also set the default notification volume to `30` (down from the upstream default of `70`) and disabled TTS by default — both changes are reflected in my local config. Works much better for late-night coding sessions.

</div>

<details>
<summary><kbd>Table of Contents</kbd></summary>

- [What's New in v5.0](#-whats-new-in-v50)
- [Install in 60 Seconds](#-install-in-60-seconds)
- [Just Say It — Natural Language Control](#-just-say-it--natural-language-control)
- [How It Works](#-how-it-works)
- [Key Features](#-key-features)
- [Technical Reference](#-technical-reference)
- [Platform Support](#-platform-support)
- [Troubleshooting](#-troubleshooting)
- [Uninstall](#-uninstall)
- [For Developers](#-for-developers)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

</details>

---

## What's New in v5.0

<details>
<summary><kbd>v5.0 — AI-first redesign (click to expand)</kbd></summary>
<br>

v5.0 is an **AI-first redesign**. Every project surface is now machine-operable end-to-end so Claude Code can install, configure, snooze, troubleshoot, and upgrade the project on a human's behalf without any clicks, prompts, or doc reading.

| Highlight | Effect |
|---|---|
| **`audio-hooks` JSON CLI** | Single binary with 27 subcommands. JSON to stdout, stable error codes + suggested commands. |
| **`/aud
