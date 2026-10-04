#!/usr/bin/env python
"""
Generate synthetic dataset for THERMALIFT prototype.

Usage:
    python -m app.data.generate_dataset [--days N] [--freq-hours H] [--output-dir DIR]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.data.synthetic_data import SyntheticDataGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate THERMALIFT synthetic dataset")
    parser.add_argument("--days", type=int, default=90, help="Number of days to generate")
    parser.add_argument("--freq-hours", type=int, default=6, help="Frequency in hours")
    parser.add_argument("--output-dir", type=str, default="data/synthetic", help="Output directory")
    parser.add_argument("--format", choices=["parquet", "csv", "both"], default="parquet", help="Output format")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating synthetic dataset: {args.days} days, {args.freq_hours}h frequency, seed={args.seed}")
    print("=" * 60)

    generator = SyntheticDataGenerator(seed=args.seed)
    all_states = generator.generate_all_wells(
        n_days=args.days,
        freq_hours=args.freq_hours
    )

    total_records = 0
    for well_id, states in all_states.items():
        print(f"\n{well_id}: {len(states)} records")
        if args.format in ["parquet", "both"]:
            path = output_dir / f"{well_id}.parquet"
            generator.save_parquet(states, str(path))
            print(f"  Saved: {path}")
        if args.format in ["csv", "both"]:
            path = output_dir / f"{well_id}.csv"
            generator.save_csv(states, str(path))
            print(f"  Saved: {path}")
        total_records += len(states)

    print(f"\n{'=' * 60}")
    print(f"Total records: {total_records} across 5 wells")
    print(f"Output directory: {output_dir.absolute()}")
    print("\nWARNING: ALL DATA IS SYNTHETIC / DEMO DATA -- NOT REAL FIELD DATA")


if __name__ == "__main__":
    main()