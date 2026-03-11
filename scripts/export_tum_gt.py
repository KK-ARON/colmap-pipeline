"""
从 TUM groundtruth.txt 文件导出 traj_gt.csv。

TUM groundtruth 格式如下：

# 注释行以 # 开头

timestamp tx ty tz qx qy qz qw

此脚本仅提取 (timestamp, tx, ty, tz)，即世界坐标系中的真实相机位置，并将其写入 traj_gt.csv，以便 ATE 与 traj_est.csv 进行对比评估。

Usage:
    python scripts/export_tum_gt.py \
        --groundtruth  data/TUM-rgb/prepared/rgbd_dataset_freiburg1_desk/groundtruth.txt \
        --output       runs/tum_freiburg1_desk/traj_gt.csv
"""

import argparse
import csv
from pathlib import Path


def export_groundtruth(groundtruth_txt: Path, output_csv: Path) -> None:
    print(f"Reading groundtruth from {groundtruth_txt} …")
    rows: list[tuple[float, float, float, float]] = []

    with open(groundtruth_txt, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            # timestamp tx ty tz qx qy qz qw  (only need first 4)
            timestamp = float(parts[0])
            tx, ty, tz = float(parts[1]), float(parts[2]), float(parts[3])
            rows.append((timestamp, tx, ty, tz))

    # Already sorted in TUM files, but sort just in case
    rows.sort(key=lambda r: r[0])

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "x", "y", "z"])
        for row in rows:
            writer.writerow([f"{row[0]:.6f}", f"{row[1]:.9f}", f"{row[2]:.9f}", f"{row[3]:.9f}"])

    print(f"Wrote {len(rows)} poses → {output_csv}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export ground-truth camera trajectory from TUM groundtruth.txt to CSV."
    )
    parser.add_argument(
        "--groundtruth",
        required=True,
        type=Path,
        help="Path to TUM groundtruth.txt",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output path for traj_gt.csv",
    )
    args = parser.parse_args()
    export_groundtruth(args.groundtruth, args.output)


if __name__ == "__main__":
    main()
