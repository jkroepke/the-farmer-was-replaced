# Reddit Dinosaur Coil/Strike Reference

## Upstream

- Reddit discussion: https://www.reddit.com/r/TheFarmerWasReplaced/comments/1p0ox9z/my_fastest_dinosaur_run/
- Primary Pastebin: https://pastebin.com/xsZL19rH
- Helper Pastebin: https://pastebin.com/z4Rxj5CE
- Reviewed: 2026-09-19
- Source type: Reddit discussion + Pastebin
- License: no explicit redistribution license found

Because no redistribution license is declared, the verbatim Pastebin source is not mirrored into this repository. See `source/UPSTREAM.md` for the source locations.

## Useful algorithm

The author describes the Dinosaur as repeating four phases:

1. **coil**: shape the tail into a predictable vertical pattern
2. **strike**: chase Apples in the open eastern area, possibly taking several when each next Apple is farther east
3. **pre-return**: move to the south-east corner when further strikes are no longer useful
4. **return**: travel back to `(0,0)` and begin the next coil

The published source then switches to a safe deterministic sweep once the tail is large enough.

A later Reddit commenter reports a substantial middlegame improvement from tracking the tail and allowing westward double-backs during the strike phase. That claim is community evidence only and has not yet been reproduced locally.

## Local benchmark representation

`bench_dinosaur.py` contains independent implementations of the published algorithm description rather than copied Pastebin code:

- mode 10: safe transition around 33% board occupancy
- mode 11: source-like safe transition around 50%
- mode 12: safe transition around 66%

The benchmark clamps the source's occasional out-of-range `world_size` movement targets to the physical farm edge. This intentionally avoids measuring repeated blocked border moves while preserving the four-phase route policy.

The source uses a timeout/recovery path. The local benchmark instead has the benchmark move watchdog and reports a failed run as invalid, because sleeping/retrying would distort route comparisons.

## Cleanup observation

The separate skysdottir Reddit/GitHub reference uses a multi-drone preparation phase that harvests the farm and converts it to Soil before equipping the Dinosaur Hat.

This matters because the current Wiki documents that Apples cannot spawn on occupied tiles and Grass grows automatically on Grassland. Whether the leaderboard's fresh starting state makes the full preparation worth its cost must therefore be measured rather than assumed.
