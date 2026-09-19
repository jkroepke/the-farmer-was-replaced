#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the Top Hat executable wrapper and import-safe controller boundary."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import top_hat  # noqa: E402,F401


def test_wrapper_only_delegates_to_controller() -> None:
    source = (SAVE_DIRECTORY / "run_top_hat.py").read_text()
    tree = ast.parse(source)

    imports = []
    calls = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            imports.append((node.module, [alias.name for alias in node.names]))
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            calls.append(node.value)

    if imports != [("top_hat", ["farm_top_hat"])]:
        raise AssertionError(f"Top Hat wrapper imports changed: {imports}")

    if len(calls) != 1:
        raise AssertionError("Top Hat wrapper performed unexpected executable work")

    call = calls[0]
    if not isinstance(call.func, ast.Name) or call.func.id != "farm_top_hat":
        raise AssertionError("Top Hat wrapper did not invoke the controller")

    if call.args or call.keywords:
        raise AssertionError("Top Hat wrapper passed unexpected controller arguments")


def test_controller_has_no_runner_imports() -> None:
    source = (SAVE_DIRECTORY / "top_hat.py").read_text()
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module.startswith("run_"):
                raise AssertionError("Top Hat controller imported an executable runner")


def main() -> None:
    test_wrapper_only_delegates_to_controller()
    test_controller_has_no_runner_imports()
    print("Passed Top Hat entry-point and import-boundary tests")


if __name__ == "__main__":
    main()
