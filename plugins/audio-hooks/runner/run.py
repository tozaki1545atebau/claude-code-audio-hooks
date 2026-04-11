#!/usr/bin/env python3
"""Plugin entry point for hook_runner.py.

This file lives at ${CLAUDE_PLUGIN_ROOT}/runner/run.py and is invoked by every
hook entry in hooks/hooks.json. It imports the canonical hook_runner.py from
the project source bundled inside the plugin and dispatches.

Why a wrapper instead of a symlink: symlinks don't survive file copy on
Windows and can confuse some plugin caching paths. A wrapper is portable and
Claude Code's plugin caching copies the source files alongside this wrapper,
so the import resolves cleanly inside the plugin cache.

Path resolution:
  - The plugin layout under .claude/plugins/cache/<id>/ contains both this
    runner/ directory and a sibling source/ tree from the marketplace clone.
  - We walk up looking for a directory containing hooks/hook_runner.py, then
    insert it into sys.path.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_hook_runner() -> Path | None:
    """Locate hooks/hook_runner.py in or above this script's directory."""
    explicit = os.environ.get("CLAUDE_AUDIO_HOOKS_PROJECT")
    if explicit:
        candidate = Path(explicit) / "hooks" / "hook_runner.py"
        if candidate.exists():
            return candidate.parent

    here = Path(__file__).resolve()
    for ancestor in [here.parent] + list(here.parents):
        # Plugin layout: ${CLAUDE_PLUGIN_ROOT}/hooks/hook_runner.py is bundled
        candidate = ancestor / "hooks" / "hook_runner.py"
        if candidate.exists():
            return candidate.parent
    return None


def main() -> int:
    hooks_dir = _find_hook_runner()
    if hooks_dir is None:
        # Structured error to stderr is acceptable here because Claude Code's
        # hook system swallows hook output by default; this branch only fires
        # if the plugin cache is corrupted.
        sys.stderr.write('{"error":"hook_runner.py not found in plugin"}\n')
        return 1

    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))

    import hook_runner  # type: ignore
    return hook_runner.main()


if __name__ == "__main__":
    sys.exit(main())
