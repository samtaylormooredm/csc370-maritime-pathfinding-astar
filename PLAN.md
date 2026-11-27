# CSC 370 project plan

## First milestone

Run A* between one verified pair of World Port Index ports in the Cyclades at one H3 resolution. Start by checking whether Paros and Naxos are suitable entries with distinct accessible water cells. Aim for a visible detour around land for the main demo. If the first pair gives a simple route, use it as a smoke test and select a second pair with a direct line that crosses land.

Start with H3 resolution 7 as a trial setting and keep it configurable. Use a bounded study region with enough space for routes to go around islands. If the graph disconnects ports or clips a plausible route, inspect the coast mask, port snapping and region bounds before selecting the resolution for the experiment.

## Work split

| Owner | First deliverable | After integration |
| --- | --- | --- |
| Sam | Implement heap-based A* in `maritime/routing.py` using the toy graph. Track best costs, skip outdated queue entries, reconstruct routes and record expanded cells. Add the zero-heuristic UCS baseline and verify expected results on the toy graph. | Run controlled comparisons, summarize results and explain how the heuristic affects search. |
| Rafae | Build `maritime/water_graph.py` and `maritime/ports.py`. Load Natural Earth land and minor islands, form water cells and valid edges, and snap WPI ports to accessible water cells. Verify the graph on one small region. | Build `maritime/plot_route.py` and generate a map with the coastline, port markers, snapped endpoints and route. |
| Both | Agree on kilometers, region bounds, endpoint representation and the first port pair. Connect both halves through `maritime/__main__.py` once the toy search and real graph work independently. | Validate mapped routes, choose demo examples and review the README, results and presentation together. |

Suggested branches after the starter lands on `main`: `astar-search` for Sam and `water-graph` for Rafae. Keep changes to the shared entry point for integration, and cross-review the two branches before merging.

## How the pieces connect

- The graph uses H3 cell IDs as strings. It exposes `neighbors(cell)`, yielding `(neighbor_id, distance_km)` pairs, and a function for looking up each cell center.
- Search accepts `start`, `goal`, `neighbors` and a two-cell `heuristic`. It returns ordered cell IDs, graph distance in kilometers and the number of expansions. An unreachable goal returns no path while preserving the expansion count.
- Use great-circle distance between cell centers for both edge weights and the direct-to-goal heuristic. With those weights, the triangle inequality makes the heuristic a lower bound on any path in the graph.
- Work with latitude and longitude at the H3 boundary and longitude and latitude when constructing EPSG:4326 Shapely geometry. Gather candidates inside the region, drop every cell whose polygon intersects mapped land and check each candidate center-to-center segment before admitting the edge. H3 and Shapely handle separate parts of this step.
- Snap each WPI coordinate to a nearby connected water cell and record the snap distance. Choose and document the maximum acceptable snap distance, flag ports with no suitable cell nearby, and show actual ports and snapped endpoints as separate markers. Report distance between snapped endpoints.
- Read input datasets from `data/raw/`. Record the source versions, CRS and study bounds in the README once selected. Add geospatial dependencies with the graph implementation.

## Checkpoints

1. **Parallel development.** Sam can test without downloading data. The toy graph should return A–B–D at 8 km, return 0 km from A to itself, and report D-to-E as unreachable. Rafae can check that the port cells exist in the same water component and that coast-adjacent cells or edges are blocked.
2. **One end-to-end route.** Run both algorithms on the same port pair and graph. Check that every consecutive pair is a graph edge and independently intersect the plotted route geometry with the combined land and minor-island layers. Show a map and the distance, search runtime and expanded-cell count.
3. **Experiment and demo.** If the first route works, use about three port pairs covering open water, an island detour and a coast-adjacent route. Record distance, mapped-land intersections, median search runtime across repeated runs and expanded cells. Build the graph once and time only search. For each pair, A* and UCS should agree on optimal distance within floating-point tolerance. Different paths of equal cost are possible.
4. **Wrap up.** Include a reproducible run command, a map with a visible land detour, and one comparison table. Discuss how resolution and coastal data affect routes. Keep depth, weather and passage restrictions as extensions.

## Data and API references

- [Natural Earth 1:10m physical vectors, including Land and Minor Islands](https://www.naturalearthdata.com/downloads/10m-physical-vectors/)
- [NGA World Port Index](https://vcps.nga.mil/nauticalpubs-feature/rest/services/WPI/World_Port_Index_Viewer/FeatureServer)
- [H3 Python API](https://uber.github.io/h3-py/api_quick.html)
