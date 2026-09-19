#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify standalone runner structure without executing infinite loops."""

from __future__ import annotations

import ast
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
RUNNERS = {
    "run_hay.py": ("hay", "farm_hay_cycle"),
    "run_carrots.py": ("carrots", "farm_carrot_cycle"),
    "run_trees.py": ("trees", "farm_tree_cycle"),
    "run_cactus.py": ("cactus", "farm_cactus_patch"),
    "run_pumpkins.py": ("pumpkins", "farm_pumpkin_cycle"),
    "run_sunflowers.py": ("sunflowers", "farm_sunflower_cycle"),
}


def get_runner_loop(tree: ast.Module, filename: str) -> ast.While:
    loops = [node for node in tree.body if isinstance(node, ast.While)]

    if len(loops) != 1:
        raise AssertionError(f"{filename} does not have one top-level loop")

    return loops[0]


def assert_import(tree: ast.Module, filename: str, module: str, function: str) -> None:
    imports = []

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            imports.append((node.module, [alias.name for alias in node.names]))

    if (module, [function]) not in imports:
        raise AssertionError(f"{filename} imports the wrong bounded operation: {imports}")


def assert_cycle_failure_breaks(loop: ast.While, filename: str) -> None:
    calls = [node for node in ast.walk(loop) if isinstance(node, ast.Call)]
    call_names = []

    for call in calls:
        if isinstance(call.func, ast.Name):
            call_names.append(call.func.id)

    if "quick_print" not in call_names or not any(
        isinstance(node, ast.Break) for node in ast.walk(loop)
    ):
        raise AssertionError(f"{filename} has no visible hard-failure exit")


def test_runner_structure() -> None:
    for filename, (module, function) in RUNNERS.items():
        source = (SAVE_DIRECTORY / filename).read_text()
        tree = ast.parse(source)
        loop = get_runner_loop(tree, filename)
        assert_import(tree, filename, module, function)
        assert_cycle_failure_breaks(loop, filename)

        if function not in [
            node.func.id
            for node in ast.walk(loop)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]:
            raise AssertionError(f"{filename} never invokes its bounded operation")

        if filename == "run_sunflowers.py":
            if not any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "num_items"
                for node in ast.walk(loop)
            ):
                raise AssertionError("sunflower runner lost its static target condition")
        elif not isinstance(loop.test, ast.Constant) or loop.test.value is not True:
            raise AssertionError(f"{filename} is not a continuous runner")

        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                raise AssertionError(f"{filename} performs work outside its runner loop")


def main() -> None:
    test_runner_structure()
    print("Passed standalone runner structure and failure-exit tests")


if __name__ == "__main__":
    main()
