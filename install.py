#!/usr/bin/env python3
"""Install Potato Mode for Claude Code, Codex, or both."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "skill" / "potato-mode"


def destination(target: str, scope: str, project: Path) -> Path:
    if scope == "personal":
        base = Path.home()
        return base / (".claude/skills/potato-mode" if target == "claude" else ".agents/skills/potato-mode")
    resolved = project.expanduser().resolve()
    return resolved / (".claude/skills/potato-mode" if target == "claude" else ".agents/skills/potato-mode")


def install(target: str, scope: str, project: Path, force: bool) -> Path:
    dest = destination(target, scope, project)
    if dest.exists():
        if not force:
            raise FileExistsError(f"{dest} already exists. Use --force to replace it.")
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, dest)
    return dest


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--target", choices=("claude", "codex", "both"))
    result.add_argument("--scope", choices=("personal", "project"), default="personal")
    result.add_argument("--project", type=Path, default=Path.cwd())
    result.add_argument("--force", action="store_true")
    return result


def choose_target() -> str:
    print("Install Potato Mode for:")
    print("  1. Claude Code")
    print("  2. Codex")
    print("  3. Both")
    answer = input("Choose 1, 2, or 3: ").strip()
    return {"1": "claude", "2": "codex", "3": "both"}.get(answer, "")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    target = args.target or choose_target()
    if target not in {"claude", "codex", "both"}:
        print("Invalid choice.", file=sys.stderr)
        return 2
    targets = ["claude", "codex"] if target == "both" else [target]
    try:
        for item in targets:
            print(f"Installed for {item}: {install(item, args.scope, args.project, args.force)}")
    except (FileExistsError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
