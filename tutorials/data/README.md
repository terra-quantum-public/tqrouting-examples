# Data

All instances in this directory are synthetic. The four plane-coordinate
instances are produced by [`generate.py`](generate.py) from fixed seeds, so
`python generate.py` recreates them byte for byte; distances are Euclidean,
rounded to one decimal, and stored as `duration_matrix` (one time unit per
distance unit). `bayern_instance.json` was generated separately with real GPS
coordinates so that the OSRM notebook can compute road-network matrices for
it. Nothing here is derived from published benchmark sets or from customer
data.

| File | Contents | Used in |
|---|---|---|
| `vrptw_100.json` | 100 customers in ten clusters, tight time windows built from a tour through each cluster, 90-unit service times, 25 vehicles of capacity 200 | `constraints.ipynb`, time windows |
| `cvrp_100.json` | 100 customers, half uniform and half in five clusters, demands 1–100, unlimited fleet of capacity 200 | `workflow.ipynb`, JSON round-trip |
| `mdvrp_100.json` | 100 customers spread over the area, two depots with five vehicles of capacity 200 each | `constraints.ipynb`, multiple depots |
| `top_100.json` | 100 customers with prizes 1–30 that grow with distance from the depot, two vehicles limited to 55 time units each | `objectives.ipynb`, prize collecting |
| `bayern_instance.json` | 500 customers with GPS coordinates around Ingolstadt, Bavaria, `HH:MM:SS` time windows and service times, two vehicle types with shifts and route limits; no matrix | `real_world_osrm.ipynb`, local OSRM |
