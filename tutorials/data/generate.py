#!/usr/bin/env python3
"""Generate the synthetic tutorial instances in this directory.

Every plane-coordinate instance here is produced by this script from a fixed
seed, so the data has no external source and can be recreated byte for byte:

    python generate.py

Coordinates are abstract plane units. Distances are Euclidean, rounded to one
decimal, and stored as ``duration_matrix`` (one time unit per distance unit),
which is what the notebooks expect when they load the files. Matrix row 0 (and
row 1 for the two-depot instance) is the depot; customers follow in order.
"""

import json
import math
import random
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent

Point = tuple[float, float]
Fields = dict[str, Any]


def euclid_matrix(points: list[Point]) -> list[list[float]]:
    """Return the full Euclidean distance matrix, rounded to one decimal."""
    return [[round(math.dist(a, b), 1) for b in points] for a in points]


def location(point: Point, matrix_id: int) -> Fields:
    """Return a location dict with both the matrix row and the plane coordinates."""
    x, y = point
    return {"matrix_id": matrix_id, "x": x, "y": y}


def write(
    name: str,
    depots: list[Point],
    customers: list[tuple[Point, Fields]],
    fleet: list[tuple[int, Fields]],
) -> None:
    """Write one instance file next to this script.

    Args:
        name: Output file name, e.g. ``"vrptw_100.json"``.
        depots: Depot points; depot ``i`` gets matrix row ``i``.
        customers: ``(point, fields)`` pairs; ``fields`` are merged into the
            customer object (loads, windows, prizes, ...).
        fleet: ``(depot_index, fields)`` pairs, one per vehicle type; each type
            starts and ends at that depot.
    """
    points = list(depots) + [p for p, _ in customers]
    out = {
        "customers": [
            {"location": location(p, len(depots) + i), **fields}
            for i, (p, fields) in enumerate(customers)
        ],
        "fleet": [
            {
                "start_location": location(depots[d], d),
                "end_location": location(depots[d], d),
                **fields,
            }
            for d, fields in fleet
        ],
    }
    body = json.dumps(out, indent=2)
    # One matrix row per line keeps the file readable and diffable. body[:-2]
    # drops the closing "\n}" of the object so the matrix can be appended as
    # its last key.
    rows = ",\n".join("    " + json.dumps(row) for row in euclid_matrix(points))
    text = body[:-2] + ',\n  "duration_matrix": [\n' + rows + "\n  ]\n}\n"
    (HERE / name).write_text(text)
    print(f"{name}: {len(customers)} customers, {len(depots)} depot(s), {len(points)}x{len(points)} matrix")


def clustered_points(
    rng: random.Random,
    n_clusters: int,
    per_cluster: int,
    lo: float,
    hi: float,
    spread: float,
    min_sep: float,
) -> list[list[tuple[int, int]]]:
    """Scatter integer points around cluster centres at least ``min_sep`` apart.

    Args:
        rng: Seeded random generator; the call order fixes the output.
        n_clusters: Number of clusters.
        per_cluster: Distinct integer points per cluster.
        lo: Lower bound of the square area, for both coordinates.
        hi: Upper bound of the square area, for both coordinates.
        spread: Standard deviation of the points around their centre.
        min_sep: Minimum distance between two cluster centres.

    Returns:
        One list of points per cluster.
    """
    centres = []
    while len(centres) < n_clusters:
        c = (rng.uniform(lo + spread, hi - spread), rng.uniform(lo + spread, hi - spread))
        if all(math.dist(c, o) >= min_sep for o in centres):
            centres.append(c)
    clusters = []
    for cx, cy in centres:
        pts = []
        while len(pts) < per_cluster:
            p = (round(rng.gauss(cx, spread)), round(rng.gauss(cy, spread)))
            if lo <= p[0] <= hi and lo <= p[1] <= hi and p not in pts:
                pts.append(p)
        clusters.append(pts)
    return clusters


def vrptw_100() -> None:
    """Ten clusters of ten customers with tight time windows.

    Windows come from a nearest-neighbour tour through each cluster, so one
    vehicle per cluster is feasible by construction; 25 vehicles leave room
    for the solver to split clusters when capacity requires it.
    """
    rng = random.Random(1)
    depot = (50, 50)
    service = 90
    customers = []
    for cluster in clustered_points(rng, 10, 10, 0, 100, spread=4, min_sep=18):
        t, pos, remaining = 0.0, depot, list(cluster)
        while remaining:
            nxt = min(remaining, key=lambda p: math.dist(pos, p))
            remaining.remove(nxt)
            arrival = t + math.dist(pos, nxt)
            width = rng.uniform(40, 90)
            before = rng.uniform(5, width - 5)
            start = max(0.0, arrival - before)
            customers.append((nxt, {
                "delivery_load": rng.choices([10, 20, 30, 40, 50], weights=[45, 35, 12, 6, 2])[0],
                "service_time": service,
                "time_window": {"start": round(start), "end": round(start + width)},
            }))
            t, pos = arrival + service, nxt
    write("vrptw_100.json", [depot], customers,
          [(0, {"capacity_load": 200, "n_vehicles": 25})])


def cvrp_100() -> None:
    """Half the customers uniform, half in five clusters; unlimited fleet."""
    rng = random.Random(2)
    depot = (rng.randint(300, 700), rng.randint(300, 700))
    points = set()
    for cluster in clustered_points(rng, 5, 10, 0, 1000, spread=40, min_sep=250):
        points.update(cluster)
    while len(points) < 100:
        points.add((rng.randint(0, 1000), rng.randint(0, 1000)))
    customers = [(p, {"delivery_load": rng.randint(1, 100)}) for p in sorted(points)]
    write("cvrp_100.json", [depot], customers, [(0, {"capacity_load": 200})])


def mdvrp_100() -> None:
    """Two depots, five vehicles each, customers spread over the whole area."""
    rng = random.Random(3)
    depots = [(20, 40), (60, 40)]
    points = set()
    while len(points) < 100:
        points.add((rng.randint(0, 80), rng.randint(0, 80)))
    customers = [(p, {"delivery_load": rng.randint(1, 30)}) for p in sorted(points)]
    write("mdvrp_100.json", depots, customers,
          [(0, {"capacity_load": 200, "n_vehicles": 5}),
           (1, {"capacity_load": 200, "n_vehicles": 5})])


def top_100() -> None:
    """Prize collecting: two vehicles, a route-duration cap, prizes 1-30.

    Prizes grow with distance from the depot plus noise, so the interesting
    customers are the far ones and the duration cap forces a choice.
    """
    rng = random.Random(4)
    depot = (15.0, 3.0)
    points = set()
    while len(points) < 100:
        points.add((round(rng.uniform(0, 30), 1), round(rng.uniform(0, 30), 1)))
    customers = []
    for p in sorted(points):
        far = math.dist(depot, p) / 30.0
        customers.append((p, {"profit": max(1, min(30, round(20 * far) + rng.randint(1, 10)))}))
    write("top_100.json", [depot], customers, [(0, {"n_vehicles": 2, "max_duration": 55})])


if __name__ == "__main__":
    vrptw_100()
    cvrp_100()
    mdvrp_100()
    top_100()
