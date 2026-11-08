#!/usr/bin/env python3
"""Measure Serial, MPI or CUDA on sparse/dense graphs and save CSV/plots."""

import argparse
import csv
from pathlib import Path
import re
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementation", choices=("serial", "mpi", "cuda"), default="serial")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--processes", type=int, nargs="+", default=[4],
                        help="MPI process counts, e.g. --processes 1 2 4 8 12")
    parser.add_argument("--mpirun", default="mpirun")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--kind", choices=("sparse", "dense"), default="sparse")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--source", type=int, default=0)
    args = parser.parse_args()
    if args.binary is None:
        args.binary = ROOT / args.implementation
    args.processes = list(dict.fromkeys(args.processes))
    process_counts = args.processes if args.implementation == "mpi" else [1]
    label = {"serial": "Serial", "mpi": "MPI", "cuda": "CUDA"}[args.implementation]
    scope = {
        "serial": "Algorithm only; excludes graph loading and printing.",
        "mpi": "Algorithm only; excludes scatter/gather, graph loading and printing.",
        "cuda": "Includes GPU allocation, transfers, kernels and cleanup; excludes graph loading/printing.",
    }[args.implementation]
    if args.output_dir is None:
        mpi_suffix = f"_mpi_np{args.processes[0]}" if len(args.processes) == 1 else "_mpi"
        suffix = {"serial": "", "mpi": mpi_suffix, "cuda": "_cuda"}[args.implementation]
        args.output_dir = ROOT / "output" / f"benchmark_{args.kind}{suffix}"
    if args.runs < 1:
        parser.error("--runs must be positive")
    if any(p < 1 for p in args.processes):
        parser.error("--processes must be positive")
    if not args.binary.is_file():
        parser.error(f"Binary not found: {args.binary}. See INSTALL.md.")

    # Check the plotting dependency before spending time on measurements.
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        parser.error("Install matplotlib: python3 -m pip install matplotlib")

    cases = []
    for path in args.data_dir.glob(f"{args.kind}_*.txt"):
        with path.open() as graph:
            n, m = map(int, graph.readline().split())
        if n <= 0 or m < 0 or not 0 <= args.source < n:
            parser.error(f"Invalid graph size/source: {path}")
        cases.append((n, m, path))
    if not cases:
        parser.error(f"No {args.kind}_*.txt files found in {args.data_dir}")
    cases.sort()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    def measure(path, processes):
        command = [str(args.binary.resolve()), str(path.resolve()), str(args.source)]
        if args.implementation == "mpi":
            command = [args.mpirun, "--oversubscribe", "-np", str(processes)] + command
        completed = subprocess.run(
            command,
            capture_output=True, text=True, check=True, timeout=300,
        )
        match = re.search(r"Execution time:\s*([0-9.eE+-]+)\s+seconds", completed.stdout)
        if not match:
            raise RuntimeError(f"Missing Execution time in output for {path}")
        return float(match.group(1))

    fields = ["file", "vertices", "edges", "source", "implementation", "processes", "timing_scope"]
    fields += [f"run{i + 1}_s" for i in range(args.runs)]
    fields += ["median_s", "min_s", "max_s"]
    rows = []
    csv_path = args.output_dir / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for processes in process_counts:
            for n, m, path in cases:
                print(f"Running {label} ({processes} processes), {path.name}: warmup + {args.runs} measurements", flush=True)
                measure(path, processes)
                times = [measure(path, processes) for _ in range(args.runs)]
                row = {"file": path.name, "vertices": n, "edges": m, "source": args.source}
                row.update(implementation=args.implementation,
                           processes=processes,
                           timing_scope=scope)
                row.update({f"run{i + 1}_s": t for i, t in enumerate(times)})
                row.update(median_s=statistics.median(times), min_s=min(times), max_s=max(times))
                writer.writerow(row)
                output.flush()
                rows.append(row)
                print(f"  V={n:>6}, E={m:>6}, median={row['median_s']:.6f} s", flush=True)

    plot_results(args, rows, plt, label, scope)


def plot_results(args, rows, plt, label, scope):
    if args.implementation == "mpi":
        fig, ax = plt.subplots(figsize=(8, 5))
        axes = [ax]
        dimensions = [("vertices", "Vertices (V)")]
    else:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        dimensions = [("vertices", "Vertices (V)"), ("edges", "Edges (E)")]
    for ax, (key, axis_label) in zip(axes, dimensions):
        for processes in sorted({row["processes"] for row in rows}):
            series = sorted((row for row in rows if row["processes"] == processes),
                            key=lambda row: row[key])
            series_label = f"MPI ({processes} processes)" if args.implementation == "mpi" else label
            ax.plot([row[key] for row in series], [row["median_s"] for row in series],
                    "o-", label=f"{series_label}: median")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ticks = sorted({row[key] for row in rows})
        ax.set_xticks(ticks, labels=[f"{value:,}" for value in ticks], rotation=30)
        ax.tick_params(axis="x", which="minor", bottom=False, labelbottom=False)
        ax.set_xlabel(f"{axis_label} — log scale")
        ax.set_ylabel("Reported execution time (seconds) — log scale")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle(f"{args.kind.capitalize()} graphs — {label}, source {args.source}, {args.runs} runs")
    if all(row["edges"] == 3 * row["vertices"] for row in rows):
        dataset_note = "Current dataset: E = 3V."
    elif all(row["edges"] == row["vertices"] * (row["vertices"] - 1) // 2 for row in rows):
        dataset_note = "Complete graphs: E = V(V-1)/2."
    else:
        dataset_note = ""
    fig.text(0.5, 0.015, f"{scope}\n{dataset_note}", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    for extension in ("png", "svg"):
        fig.savefig(args.output_dir / f"time_vs_size.{extension}", dpi=180)
    plt.close(fig)
    print(f"Saved table and plots to {args.output_dir.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(f"Command failed: {' '.join(error.cmd)}\n{error.stderr}", file=sys.stderr)
        sys.exit(1)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
