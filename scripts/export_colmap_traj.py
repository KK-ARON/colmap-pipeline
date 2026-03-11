"""
从 COLMAP 稀疏重建导出 traj_est.csv 文件。

对于每个已配准的图像，计算相机中心：
C = -R^T @ t

其中 R 由存储在 images.txt 中的四元数 (qw, qx, qy, qz) 导出，
t = (tx, ty, tz) 为平移向量。

输出为 CSV 文件，包含以下列：timestamp、x、y、z

按时间戳排序，可用于与 traj_gt.csv 进行 ATE 评估。

Usage:
    python scripts/export_colmap_traj.py \
        --images_txt   runs/tum_freiburg1_desk/colmap_output/sparse/0/images.txt \
        --ts_mapping   data/TUM-rgb/prepared/rgbd_dataset_freiburg1_desk/timestamp_mapping.csv \
        --output       runs/tum_freiburg1_desk/traj_est.csv
"""

import argparse
import csv
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def quat_to_rotation_matrix(qw: float, qx: float, qy: float, qz: float) -> np.ndarray:
    """Return 3x3 rotation matrix from a unit quaternion (qw, qx, qy, qz)."""
    # Pre-compute repeated products
    x2, y2, z2 = 2 * qx * qx, 2 * qy * qy, 2 * qz * qz
    xy, xz, yz = 2 * qx * qy, 2 * qx * qz, 2 * qy * qz
    wx, wy, wz = 2 * qw * qx, 2 * qw * qy, 2 * qw * qz

    return np.array([
        [1 - y2 - z2,  xy - wz,     xz + wy    ],
        [xy + wz,      1 - x2 - z2, yz - wx    ],
        [xz - wy,      yz + wx,     1 - x2 - y2],
    ])


def camera_center(qw, qx, qy, qz, tx, ty, tz) -> np.ndarray:
    """Return world-space camera center C = -R^T @ t."""
    R = quat_to_rotation_matrix(qw, qx, qy, qz)
    t = np.array([tx, ty, tz])
    return -R.T @ t


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def load_timestamp_mapping(csv_path: Path) -> dict[str, float]:
    """
    Load filename → timestamp mapping produced by preprocess_tum.py.

    CSV format (with header):
        filename,timestamp
        000000.png,1305031910.765238
    """
    mapping: dict[str, float] = {}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row["filename"]] = float(row["timestamp"])
    return mapping


def parse_images_txt(images_txt: Path):
    """
    Parse COLMAP images.txt and yield (name, qw, qx, qy, qz, tx, ty, tz)
    for every registered image.

    File format (two lines per image, comment lines start with #):
        IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID NAME
        POINT2D[] as (X Y POINT3D_ID) ...
    """
    with open(images_txt, "r") as f:
        lines = f.readlines()

    i = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        i += 1
        if i % 2 == 1:
            # Odd non-comment line → image pose line
            parts = line.split()
            # IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID NAME
            # index:   0  1  2  3  4  5  6  7         8  9
            if len(parts) < 10:
                continue
            name = parts[9]
            qw, qx, qy, qz = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
            tx, ty, tz     = float(parts[5]), float(parts[6]), float(parts[7])
            yield name, qw, qx, qy, qz, tx, ty, tz
        # Even line is the 2D keypoints — skip


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def export_trajectory(
    images_txt: Path,
    ts_mapping_csv: Path,
    output_csv: Path,
) -> None:
    print(f"Loading timestamp mapping from {ts_mapping_csv} …")
    ts_map = load_timestamp_mapping(ts_mapping_csv)

    print(f"Parsing COLMAP images.txt from {images_txt} …")
    rows: list[tuple[float, float, float, float]] = []  # (timestamp, x, y, z)
    skipped = 0

    for name, qw, qx, qy, qz, tx, ty, tz in parse_images_txt(images_txt):
        if name not in ts_map:
            skipped += 1
            continue
        timestamp = ts_map[name]
        C = camera_center(qw, qx, qy, qz, tx, ty, tz)
        rows.append((timestamp, C[0], C[1], C[2]))

    if skipped:
        print(f"  Warning: {skipped} image(s) had no timestamp mapping entry and were skipped.")

    # Sort by timestamp
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
        description="Export estimated camera trajectory from COLMAP sparse model to CSV."
    )
    parser.add_argument(
        "--images_txt",
        required=True,
        type=Path,
        help="Path to COLMAP sparse/0/images.txt",
    )
    parser.add_argument(
        "--ts_mapping",
        required=True,
        type=Path,
        help="Path to timestamp_mapping.csv produced by preprocess_tum.py",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output path for traj_est.csv",
    )
    args = parser.parse_args()

    export_trajectory(
        images_txt=args.images_txt,
        ts_mapping_csv=args.ts_mapping,
        output_csv=args.output,
    )


if __name__ == "__main__":
    main()
