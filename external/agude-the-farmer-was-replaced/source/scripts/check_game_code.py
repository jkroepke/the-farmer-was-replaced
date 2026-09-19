#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Validate tracked The Farmer Was Replaced source files."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


UNSUPPORTED_NODES: dict[type[ast.AST], str] = {
    ast.AsyncFor: "async for loops",
    ast.AsyncFunctionDef: "async functions",
    ast.AsyncWith: "async context managers",
    ast.Await: "await expressions",
    ast.ClassDef: "classes",
    ast.DictComp: "dictionary comprehensions",
    ast.GeneratorExp: "generator expressions",
    ast.IfExp: "ternary expressions",
    ast.Lambda: "lambdas",
    ast.ListComp: "list comprehensions",
    ast.SetComp: "set comprehensions",
    ast.Starred: "starred expressions",
    ast.Try: "exception handling",
}


@dataclass(frozen=True, order=True)
class Finding:
    path: Path
    line: int
    column: int
    message: str

    def render(self, root: Path) -> str:
        try:
            display_path = self.path.relative_to(root)
        except ValueError:
            display_path = self.path

        return f"{display_path}:{self.line}:{self.column}: {self.message}"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check game scripts for syntax unsupported by the game interpreter."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or save directories to check; defaults to tracked Save* Python files.",
    )
    parser.add_argument(
        "--api-manifest",
        type=Path,
        default=Path("game-api.json"),
        help="Committed game API manifest (default: game-api.json).",
    )
    return parser.parse_args()


def tracked_game_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--", "*.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    return sorted(
        root / relative_path
        for relative_path in result.stdout.splitlines()
        if Path(relative_path).name != "__builtins__.py"
        and any(part.startswith("Save") for part in Path(relative_path).parts)
    )


def expand_paths(paths: list[Path], root: Path) -> list[Path]:
    if not paths:
        return tracked_game_files(root)

    files: set[Path] = set()
    for path in paths:
        resolved_path = path if path.is_absolute() else root / path
        if resolved_path.is_dir():
            files.update(resolved_path.rglob("*.py"))
        else:
            files.add(resolved_path)

    return sorted(path for path in files if path.name != "__builtins__.py")


def find_save_directory(path: Path) -> Path | None:
    for directory in path.parents:
        if directory.name.startswith("Save"):
            return directory
    return None


def module_exists(save_directory: Path, module_name: str) -> bool:
    module_path = save_directory.joinpath(*module_name.split("."))
    return module_path.with_suffix(".py").is_file() or (module_path / "__init__.py").is_file()


def import_findings(path: Path, tree: ast.AST) -> list[Finding]:
    findings: list[Finding] = []
    save_directory = find_save_directory(path)
    if save_directory is None:
        return [Finding(path, 1, 1, "file is not inside a Save* directory")]

    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                findings.append(
                    Finding(
                        path,
                        node.lineno,
                        node.col_offset + 1,
                        "relative imports are unsupported",
                    )
                )
                continue
            if node.module:
                modules = [node.module]

        for module_name in modules:
            if not module_exists(save_directory, module_name):
                findings.append(
                    Finding(
                        path,
                        node.lineno,
                        node.col_offset + 1,
                        f"import {module_name!r} does not resolve inside {save_directory.name}",
                    )
                )

    return findings


def dialect_findings(path: Path, tree: ast.AST) -> list[Finding]:
    findings: list[Finding] = []

    for node in ast.walk(tree):
        unsupported_feature = UNSUPPORTED_NODES.get(type(node))
        if unsupported_feature:
            findings.append(
                Finding(
                    path,
                    getattr(node, "lineno", 1),
                    getattr(node, "col_offset", 0) + 1,
                    f"unsupported game syntax: {unsupported_feature}",
                )
            )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = node.args
            if arguments.vararg or arguments.kwarg or arguments.kwonlyargs:
                findings.append(
                    Finding(
                        path,
                        node.lineno,
                        node.col_offset + 1,
                        "unsupported game syntax: variadic or keyword-only parameters",
                    )
                )

        if isinstance(node, ast.Call) and node.keywords:
            findings.append(
                Finding(
                    path,
                    node.lineno,
                    node.col_offset + 1,
                    "unsupported game syntax: named or expanded keyword arguments",
                )
            )

    return findings


def none_comparison_findings(path: Path, tree: ast.AST) -> list[Finding]:
    findings: list[Finding] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue

        for operator, comparator in zip(node.ops, node.comparators, strict=True):
            if not isinstance(operator, (ast.Is, ast.IsNot)):
                continue
            if not (isinstance(comparator, ast.Constant) and comparator.value is None) and not (
                isinstance(node.left, ast.Constant) and node.left.value is None
            ):
                continue

            findings.append(
                Finding(
                    path,
                    node.lineno,
                    node.col_offset + 1,
                    "game code must compare None with == or !=, not is or is not",
                )
            )

    return findings


def locally_defined_callables(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
    return names


def accepts_positional_count(signatures: list[dict[str, int | None]], count: int) -> bool:
    return any(
        count >= signature["min_positional"]
        and (signature["max_positional"] is None or count <= signature["max_positional"])
        for signature in signatures
    )


def api_findings(path: Path, tree: ast.AST, manifest: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    functions = manifest["functions"]
    enums = manifest["enums"]
    local_callables = locally_defined_callables(tree)

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in functions
            and node.func.id not in local_callables
            and not any(isinstance(argument, ast.Starred) for argument in node.args)
            and not accepts_positional_count(functions[node.func.id], len(node.args))
        ):
            findings.append(
                Finding(
                    path,
                    node.lineno,
                    node.col_offset + 1,
                    f"{node.func.id}() does not accept {len(node.args)} positional argument(s)",
                )
            )
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in enums
            and node.attr not in enums[node.value.id]
        ):
            findings.append(
                Finding(
                    path,
                    node.lineno,
                    node.col_offset + 1,
                    f"{node.value.id}.{node.attr} is not in the installed game API",
                )
            )

    return findings


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported or missing schema_version")
    if not isinstance(manifest.get("functions"), dict) or not isinstance(
        manifest.get("enums"), dict
    ):
        raise ValueError("functions and enums must be objects")
    return manifest


def check_file(path: Path, manifest: dict[str, Any]) -> list[Finding]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        return [Finding(path, 1, 1, f"cannot read file: {error}")]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return [
            Finding(
                path,
                error.lineno or 1,
                error.offset or 1,
                f"Python parser error: {error.msg}",
            )
        ]

    return (
        dialect_findings(path, tree)
        + none_comparison_findings(path, tree)
        + import_findings(path, tree)
        + api_findings(path, tree, manifest)
    )


def main() -> int:
    arguments = parse_arguments()
    root = Path.cwd().resolve()

    try:
        manifest_path = (
            arguments.api_manifest
            if arguments.api_manifest.is_absolute()
            else root / arguments.api_manifest
        )
        manifest = load_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"cannot load game API manifest: {error}", file=sys.stderr)
        return 2

    try:
        files = expand_paths(arguments.paths, root)
    except subprocess.CalledProcessError as error:
        print(f"failed to list tracked files: {error}", file=sys.stderr)
        return 2

    if not files:
        print("no game Python files found", file=sys.stderr)
        return 2

    findings = sorted(finding for path in files for finding in check_file(path, manifest))
    if findings:
        for finding in findings:
            print(finding.render(root))
        print(f"Found {len(findings)} game-code error(s).")
        return 1

    print(f"Checked {len(files)} game files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
