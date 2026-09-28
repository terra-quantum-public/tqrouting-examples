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

HERE = Path(__file__).parent


def euclid_matrix(points):
    return [[round(math.dist(a, b), 1) for b in points] for a in points]


def location(point, matrix_id):
    x, y = point
    return {"matrix_id": matrix_id, "x": x, "y": y}


def write(name, depots, customers, fleet):
    """customers: list of (point, fields); fleet: list of (depot_index, fields)."""
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
    rows = ",\n".join("    " + json.dumps(row) for row in euclid_matrix(points))
    text = body[:-2] + ',\n  "duration_matrix": [\n' + rows + "\n  ]\n}\n"
    (HERE / name).write_text(text)
    print(f"{name}: {len(customers)} customers, {len(depots)} depot(s), {len(points)}x{len(points)} matrix")


def clustered_points(rng, n_clusters, per_cluster, lo, hi, spread, min_sep):
    """Cluster centres at least min_sep apart, customers scattered around them."""
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


def vrptw_100():
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


def cvrp_100():
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


def mdvrp_100():
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


def top_100():
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
