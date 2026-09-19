---
status: pending
created: "2026-09-18T05:35:12.583622+00:00"
updated: "2026-09-18T05:35:12.583635+00:00"
deps:
  - 02-complete-top-hat-follow-up-fixes
approach: Run reduced-target and full in-game validation after the static planner fixes.
criteria:
  - Initial Power fills to the adaptive high target
  - Between-watermark Power does not trigger sunflower farming
  - Low-watermark Power refills continuously to high target
  - Fertilizer waits do not cause a sunflower cycle after every flip
files:
  - plan.md
  - Save0/run_top_hat.py
---

# Validate Top Hat in game (Task 14)
