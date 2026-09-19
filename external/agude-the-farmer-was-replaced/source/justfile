ruff_version := "0.16.0"
python_version := "3.12.3"

default:
    @just --list

# Install the Python interpreter used by repository checks. Ruff remains a
# pinned, isolated uvx tool because this repository is not a Python package.
sync:
    uv python install {{python_version}}

# Run every read-only static check used by CI.
lint:
    uv run scripts/sync_game_api.py --check
    uvx ruff@{{ruff_version}} check .
    uvx ruff@{{ruff_version}} format --check .
    uv run scripts/check_game_code.py
    uv run scripts/check_skills.py

format:
    uvx ruff@{{ruff_version}} format .
    uvx ruff@{{ruff_version}} check --fix scripts

# Refresh committed API metadata after the game regenerates its editor stub.
api-sync:
    uv run scripts/sync_game_api.py

# Run the CPython cactus-sort harness against simulated game operations.
cactus-test:
    uv run scripts/test_cactus_sort.py

# Run the CPython layout classifier harness.
farm-layout-test:
    uv run scripts/test_farm_layout.py

# Run the CPython sunflower lifecycle harness.
sunflower-test:
    uv run scripts/test_sunflowers.py

# Run the CPython maze solver harness.
maze-test:
    uv run scripts/test_maze.py

# Run the CPython dinosaur-route and policy harness.
dinosaur-test:
    uv run scripts/test_dinosaurs.py

# Run the regular farming traversal integration harness.
regular-farming-test:
    uv run scripts/test_regular_farming.py

# Run the CPython fertilizer-policy harness.
fertilizing-test:
    uv run scripts/test_fertilizing.py

# Run the CPython indexed-drone dispatch harness.
parallel-farming-test:
    uv run scripts/test_parallel_farming.py

# Run the CPython shared traversal harness.
traversal-test:
    uv run scripts/test_traversal.py

# Run the CPython planting failure harness.
planting-test:
    uv run scripts/test_planting.py

# Run the CPython bounded hay harness.
hay-test:
    uv run scripts/test_hay.py

# Run the CPython bounded carrot harness.
carrot-test:
    uv run scripts/test_carrots.py

# Run the CPython bounded tree harness.
tree-test:
    uv run scripts/test_trees.py

# Run the CPython bounded pumpkin harness.
pumpkin-test:
    uv run scripts/test_pumpkins.py

# Run the CPython bounded cactus-cycle harness.
cactus-cycle-test:
    uv run scripts/test_cactus_cycle.py

# Run the CPython bounded sunflower-cycle harness.
sunflower-cycle-test:
    uv run scripts/test_sunflower_cycle.py

# Run the CPython live resource-cost harness.
resource-cost-test:
    uv run scripts/test_resource_costs.py

# Run the CPython Top Hat planner harness.
top-hat-test:
    uv run scripts/test_top_hat.py

# Run the CPython Top Hat entry-point harness.
top-hat-entry-test:
    uv run scripts/test_top_hat_entry.py

# Run the AST harness for continuous standalone runners.
runner-test:
    uv run scripts/test_runners.py

check: lint cactus-test farm-layout-test sunflower-test maze-test dinosaur-test regular-farming-test fertilizing-test parallel-farming-test traversal-test planting-test hay-test carrot-test tree-test pumpkin-test cactus-cycle-test sunflower-cycle-test resource-cost-test top-hat-test top-hat-entry-test runner-test

hooks-install:
    ln -sf ../../bin/pre-commit.sh .git/hooks/pre-commit
