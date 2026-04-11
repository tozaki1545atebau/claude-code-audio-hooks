#!/usr/bin/env python3
"""generate-audio.py — non-interactive audio file generator via ElevenLabs.

Reads config/audio_manifest.json and generates any missing audio files via
the ElevenLabs API. Voice files use the text-to-speech endpoint; sound
effects use the sound-generation endpoint. The script is designed to be
re-runnable: by default it skips files that already exist on disk.

Authentication:
    Reads ELEVENLABS_API_KEY from the environment. The key is never
    written to disk, never logged, never committed.

Usage:
    ELEVENLABS_API_KEY=<key> python scripts/generate-audio.py
    ELEVENLABS_API_KEY=<key> python scripts/generate-audio.py --force
    ELEVENLABS_API_KEY=<key> python scripts/generate-audio.py --only permission-denied.mp3,task-created.mp3
    ELEVENLABS_API_KEY=<key> python scripts/generate-audio.py --dry-run

Output:
    One JSON line per file (NDJSON) on stdout, plus a final summary JSON.
    Exit 0 if everything succeeded; exit 1 on any failure.

Hard rules (AI-first):
    - No interactive prompts.
    - No colors, no spinners.
    - All output is structured JSON.
    - On API errors, the JSON line includes the API status code and body.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "config" / "audio_manifest.json"
AUDIO_DIR = REPO_ROOT / "audio"

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"


def _emit(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _http_post_json(url: str, body: Dict[str, Any], headers: Dict[str, str], timeout: int = 60) -> bytes:
    """POST JSON, return raw response body. Raises urllib.error.HTTPError on non-2xx."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _generate_voice(api_key: str, voice_id: str, text: str, model: str, voice_settings: Dict[str, Any]) -> bytes:
    url = f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    body = {
        "text": text,
        "model_id": model,
        "voice_settings": voice_settings,
    }
    return _http_post_json(url, body, headers)


def _generate_sound_effect(api_key: str, text: str, duration_seconds: float, prompt_influence: float) -> bytes:
    url = f"{ELEVENLABS_BASE}/sound-generation"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    body = {
        "text": text,
        "duration_seconds": duration_seconds,
        "prompt_influence": prompt_influence,
    }
    return _http_post_json(url, body, headers)


def _resolve_output_path(filename: str, theme: str) -> Path:
    return AUDIO_DIR / theme / filename


def _process_one(entry: Dict[str, Any], manifest: Dict[str, Any], api_key: str,
                 force: bool, dry_run: bool) -> Dict[str, Any]:
    filename = entry["filename"]
    theme = entry["theme"]
    kind = entry["type"]
    text = entry.get("text", "")

    out_path = _resolve_output_path(filename, theme)
    result: Dict[str, Any] = {
        "filename": filename,
        "theme": theme,
        "type": kind,
        "path": str(out_path),
    }

    if not text:
        result["status"] = "skipped"
        result["reason"] = "no text in manifest"
        return result

    if out_path.exists() and not force:
        result["status"] = "skipped"
        result["reason"] = "already exists"
        result["bytes"] = out_path.stat().st_size
        return result

    if dry_run:
        result["status"] = "dry-run"
        return result

    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        start = time.time()
        if kind == "voice":
            voice_id = entry.get("voice_id") or manifest.get("_default_voice_id")
            if not voice_id:
                result["status"] = "failed"
                result["error"] = "no voice_id in entry or manifest defaults"
                return result
            model = entry.get("model") or manifest.get("_tts_model", "eleven_multilingual_v2")
            voice_settings = entry.get("voice_settings") or manifest.get("_voice_settings", {
                "stability": 0.5,
                "similarity_boost": 0.75,
            })
            audio = _generate_voice(api_key, voice_id, text, model, voice_settings)
        elif kind == "sound_effect":
            defaults = manifest.get("_sound_effect_defaults", {})
            duration = float(entry.get("duration_seconds", defaults.get("duration_seconds", 1.5)))
            prompt_influence = float(entry.get("prompt_influence", defaults.get("prompt_influence", 0.3)))
            audio = _generate_sound_effect(api_key, text, duration, prompt_influence)
        else:
            result["status"] = "failed"
            result["error"] = f"unknown type: {kind}"
            return result

        if not audio or len(audio) < 100:
            result["status"] = "failed"
            result["error"] = f"empty or truncated response ({len(audio) if audio else 0} bytes)"
            return result

        out_path.write_bytes(audio)
        result["status"] = "generated"
        result["bytes"] = len(audio)
        result["duration_ms"] = int((time.time() - start) * 1000)
        return result

    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        result["status"] = "failed"
        result["error"] = f"HTTP {e.code}: {e.reason}"
        if body:
            result["api_response"] = body
        return result
    except urllib.error.URLError as e:
        result["status"] = "failed"
        result["error"] = f"URLError: {e.reason}"
        return result
    except Exception as e:
        result["status"] = "failed"
        result["error"] = f"{type(e).__name__}: {e}"
        return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate project audio files via ElevenLabs.")
    parser.add_argument("--force", action="store_true", help="Regenerate even if file exists")
    parser.add_argument("--only", type=str, default=None, help="Comma-separated filenames to limit generation")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without calling the API")
    parser.add_argument("--manifest", type=str, default=str(MANIFEST_PATH), help="Path to audio manifest JSON")
    args = parser.parse_args(argv)

    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not args.dry_run and not api_key:
        _emit({
            "ok": False,
            "error": {
                "code": "MISSING_API_KEY",
                "message": "ELEVENLABS_API_KEY environment variable is not set.",
                "hint": "Export it before running: export ELEVENLABS_API_KEY=<key>",
            },
        })
        return 1

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        _emit({
            "ok": False,
            "error": {
                "code": "MANIFEST_NOT_FOUND",
                "message": f"Manifest not found at {manifest_path}",
            },
        })
        return 1

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _emit({"ok": False, "error": {"code": "INVALID_MANIFEST", "message": str(e)}})
        return 1

    files: List[Dict[str, Any]] = manifest.get("files", [])
    if args.only:
        wanted = {f.strip() for f in args.only.split(",") if f.strip()}
        files = [f for f in files if f.get("filename") in wanted]
        if not files:
            _emit({"ok": False, "error": {"code": "NO_MATCHING_FILES", "message": f"No manifest entries match: {sorted(wanted)}"}})
            return 1

    results: List[Dict[str, Any]] = []
    for entry in files:
        result = _process_one(entry, manifest, api_key, args.force, args.dry_run)
        _emit(result)
        results.append(result)

    generated = sum(1 for r in results if r.get("status") == "generated")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    failed = sum(1 for r in results if r.get("status") == "failed")
    dry_runs = sum(1 for r in results if r.get("status") == "dry-run")

    _emit({
        "ok": failed == 0,
        "summary": {
            "total": len(results),
            "generated": generated,
            "skipped": skipped,
            "failed": failed,
            "dry_run": dry_runs,
        },
    })

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
