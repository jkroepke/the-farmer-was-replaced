#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Validate the portable structure and local links of repository skills."""

from __future__ import annotations

import re
from pathlib import Path


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"\[[^]]*]\(([^)]+)\)")


def parse_frontmatter(path: Path, lines: list[str]) -> tuple[dict[str, str], list[str]]:
    if not lines or lines[0] != "---":
        return {}, [f"{path}:1: missing opening YAML frontmatter delimiter"]

    try:
        closing_index = lines.index("---", 1)
    except ValueError:
        return {}, [f"{path}:1: missing closing YAML frontmatter delimiter"]

    fields: dict[str, str] = {}
    errors: list[str] = []
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        if ":" not in line:
            errors.append(f"{path}:{line_number}: invalid frontmatter field")
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()

    return fields, errors


def validate_skill(path: Path, root: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return [f"{path}: cannot read file: {error}"]

    lines = text.splitlines()
    fields, errors = parse_frontmatter(path, lines)
    name = fields.get("name", "")
    description = fields.get("description", "")

    if not NAME_PATTERN.fullmatch(name):
        errors.append(f"{path}: invalid or missing skill name")
    elif name != path.parent.name:
        errors.append(f"{path}: skill name does not match parent directory")

    if not description:
        errors.append(f"{path}: missing skill description")
    elif len(description) > 1024:
        errors.append(f"{path}: skill description exceeds 1024 characters")

    if len(lines) > 500:
        errors.append(f"{path}: SKILL.md exceeds 500 lines")

    for target in LINK_PATTERN.findall(text):
        if target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        local_target = target.split("#", 1)[0]
        if local_target and not (path.parent / local_target).resolve().exists():
            relative_path = path.relative_to(root)
            errors.append(f"{relative_path}: broken local link: {target}")

    return errors


def main() -> int:
    root = Path.cwd().resolve()
    skill_files = sorted((root / ".agents" / "skills").glob("*/SKILL.md"))
    if not skill_files:
        print("no repository skills found")
        return 0

    errors = [error for path in skill_files for error in validate_skill(path, root)]
    if errors:
        for error in errors:
            print(error)
        print(f"Found {len(errors)} skill error(s).")
        return 1

    print(f"Checked {len(skill_files)} repository skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
