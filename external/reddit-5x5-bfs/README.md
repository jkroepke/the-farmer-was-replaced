# Reddit 32x5x5 map+BFS Maze reference

## Upstream

- Reddit:
  https://www.reddit.com/r/TheFarmerWasReplaced/comments/1ra25ta/my_solution_for_the_maze_33mil_goldmin/
- Post title: "My solution for the MAZE - 3.3mil gold/min"
- Published: 2026-02-20
- Reviewed: 2026-09-19

## Source-described architecture

The author describes this exact high-level lifecycle:

1. choose the largest equal Maze size that fits the farm while using all drones
2. for 32x32 with 32 drones, use 32 independent 5x5 Mazes
3. move each drone to the center of its own Maze and create it
4. map every cell in the fresh Maze with a right-hand wall-following traversal
5. store local wall connectivity per cell
6. use BFS on that map to find the shortest route to the measured Treasure
7. while following a route, detect newly opened walls caused by Maze reuse and update the map
8. reuse the Maze 300 times
9. harvest the final Treasure, create a fresh Maze, and map it again

The post reports 3.3M Gold/min in the author's environment. That is community-reported historical data, not a repository benchmark result.

## Benchmark adaptation

Mode 15, `ref-reddit5-map-bfs-reuse300`, reconstructs the described architecture:

- 32 non-overlapping 5x5 slots selected from a 6x6 grid of possible slots
- one drone per Maze
- right-hand fresh-Maze mapping
- adjacency graph
- BFS route to each measured Treasure
- learn newly opened walls while following routes
- reuse cap 300
- fixed repository Gold target and PASS/FAIL validation

No source code was published in the Reddit post. This mode is therefore a
**source-described reconstruction**, not a byte-for-byte or 1:1 code port.

Related mutations use the same map+BFS solver on 4x4 or non-uniform packed
layouts so geometry can be isolated from solver architecture.
