# Reddit normal-farm / Sunflower research

Canonical sources reviewed on 2026-09-19:

- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1pxb31j/sunflower_help/
- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1qfv72c/just_spent_hours_making_sunflowers_work/
- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1vsh1qj/i_was_inspired/
- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1v6mnwx/i_need_help_to_optimize/
- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1oe5ykd/so_is_polyculture_a_thing/

Source type: Reddit community discussions.

These discussions are optimization observations, not authoritative game mechanics.

Useful benchmark ideas:

- compare simple harvest/replant Sunflowers against max-petal ordering rather than assuming the 8x mechanic wins after interpreter/movement overhead
- compare one drone per row/column with smaller fixed rectangles
- benchmark 32 drones separately from intermediate Megafarm levels
- water plants at planting time rather than continuously topping them up
- treat Polyculture rerolling as a separate throughput experiment rather than silently folding it into a layout benchmark

One reported experiment in the Sunflower discussion measured a simple 32-drone harvest/replant farm much faster than that author's ordered-petal implementation. Another discussion describes synchronized 4x8 chunks for max-petal harvesting. These are competing community observations and are intentionally treated as benchmark candidates rather than conclusions.

No Reddit body is mirrored here. See source/UPSTREAM.md.
