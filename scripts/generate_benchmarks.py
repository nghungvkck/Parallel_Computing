#!/usr/bin/env python3
"""Generate benchmark inputs only; never launch Serial, MPI or CUDA."""

import argparse
import csv
import hashlib
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "data"
# Tables I/II, page 4 of 2504.03667v1.pdf, plus the existing extension cases.
CASES = [("sparse", n, 3 * n) for n in (10, 100, 1000, 2000, 5000, 10000, 20000)] + [
    ("dense", n, n * (n - 1) // 2) for n in (10, 100, 1000, 2000, 3000)
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DESTINATION)
    parser.add_argument("--overwrite", action="store_true",
                        help="Regenerate existing graph files; default keeps them unchanged")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = args.output_dir / "manifest.csv"
    previous = {}
    if manifest.exists():
        with manifest.open(newline="", encoding="ascii") as source:
            previous = {row["file"]: row for row in csv.DictReader(source)}
    rows = []
    for kind, n, m in CASES:
        seed = 42 + n + (1_000_000 if kind == "dense" else 0)
        rng = random.Random(seed)
        name = f"{kind}_{n}_{m}.txt"
        path = args.output_dir / name
        created = args.overwrite or not path.exists()
        if created:
            edges = sparse_edges(n, rng) if kind == "sparse" else (
                (u, v) for u in range(n) for v in range(u + 1, n)
            )
            with path.open("w", encoding="ascii", newline="\n") as output:
                output.write(f"{n} {m}\n")
                for u, v in edges:
                    output.write(f"{u} {v} {rng.randint(1, 100)}\n")
        else:
            with path.open(encoding="ascii") as source:
                if tuple(map(int, source.readline().split())) != (n, m):
                    raise ValueError(f"Unexpected graph header: {path}")
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        if not created:
            old = previous.get(name)
            if old is None or old["sha256"] != digest.hexdigest():
                raise ValueError(f"Cannot verify seed for existing file: {path}; use a new --output-dir")
            seed = old["seed"]
        rows.append({
            "file": name, "kind": kind, "vertices": n, "edges": m,
            "source": 0, "seed": seed,
            "matrix_mb": f"{4 * n * n / 1_000_000:.2f}",
            "file_bytes": path.stat().st_size, "sha256": digest.hexdigest(),
        })
        print(f"{'Created' if created else 'Kept'} {name}")
    with manifest.open("w", newline="", encoding="ascii") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
