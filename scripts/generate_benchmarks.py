#!/usr/bin/env python3
"""Generate benchmark inputs only; never launch Serial, MPI or CUDA."""

import csv
import hashlib
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "data" / "benchmarks"
CASES = [("sparse", n) for n in (100, 1000, 2000, 5000, 10000)] + [
    ("dense", n) for n in (100, 1000, 2000)
]


def sparse_edges(n, rng):
    # A random spanning tree ensures every vertex is reachable from source 0.
    order = list(range(n))
    rng.shuffle(order)
    edges = set()
    for i in range(1, n):
        u, v = order[i], order[rng.randrange(i)]
        edges.add((min(u, v), max(u, v)))
    while len(edges) < 3 * n:
        u, v = rng.randrange(n), rng.randrange(n)
        if u != v:
            edges.add((min(u, v), max(u, v)))
    # Sorting also makes output independent of set iteration order.
    return sorted(edges)


def main():
    DESTINATION.mkdir(parents=True, exist_ok=True)
    rows = []
    for kind, n in CASES:
        seed = 42 + n + (1_000_000 if kind == "dense" else 0)
        rng = random.Random(seed)
        m = 3 * n if kind == "sparse" else n * (n - 1) // 2
        name = f"{kind}_{n}_{m}.txt"
        path = DESTINATION / name
        edges = sparse_edges(n, rng) if kind == "sparse" else (
            (u, v) for u in range(n) for v in range(u + 1, n)
        )
        with path.open("w", encoding="ascii", newline="\n") as output:
            output.write(f"{n} {m}\n")
            for u, v in edges:
                output.write(f"{u} {v} {rng.randint(1, 100)}\n")
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        rows.append({
            "file": name, "kind": kind, "vertices": n, "edges": m,
            "source": 0, "seed": seed,
            "matrix_mb": f"{4 * n * n / 1_000_000:.2f}",
            "file_bytes": path.stat().st_size, "sha256": digest.hexdigest(),
        })
        print(f"Created {name}")
    with (DESTINATION / "manifest.csv").open("w", newline="", encoding="ascii") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
