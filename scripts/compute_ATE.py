"""
计算 ATE (Absolute Trajectory Error) - Position Only
使用 Umeyama 算法进行 Sim(3) 对齐（scale + rotation + translation）
"""
import argparse
import csv
from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np

# ==================== 本轮可手动修改参数 ====================
DATASET = "TUM"
SEQUENCE = "tum_freiburg1_desk"
CONFIG = "baseline"
RUN_ID = "tum_freiburg1_desk_baseline_002"

OUTPUT_DIR = Path(f"runs/{RUN_ID}")
TRAJ_EST_DIR = Path(f"runs/{RUN_ID}/traj_est.csv")
TRAJ_GT_DIR = Path(f"runs/{RUN_ID}/traj_gt.csv")
# ===========================================================
def load_trajectory(csv_path: Path) -> np.ndarray:
    """
    加载轨迹 CSV 文件
    
    格式：timestamp,x,y,z
    
    返回：
        timestamps: (N,) array
        positions: (N, 3) array
    """
    timestamps = []
    positions = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamps.append(float(row["timestamp"]))
            positions.append([float(row["x"]), float(row["y"]), float(row["z"])])
    return np.array(timestamps), np.array(positions)

def associate_timestamps(ts_est: np.ndarray, ts_gt: np.ndarray, max_diff: float = 0.02) -> list[tuple[int, int]]:
    """
    最近邻时间戳对齐
    
    参数：
        ts_est: 估计轨迹的时间戳 (N_est,)
        ts_gt: 真实轨迹的时间戳 (N_gt,)
        max_diff: 最大允许的时间戳差异（秒）
    返回：
        matches: [(est_idx, gt_idx), ...]
    """
    matches = []
    for i, x in enumerate(ts_est):
        differs = np.abs(ts_gt - x)
        j = np.argmin(differs)
        if differs[j] < max_diff:
            matches.append((i, j))
    return matches

def umeyama_alignment(P_est: np.ndarray, P_gt: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """
    Umeyama 算法：计算 Sim(3) 对齐参数
    
    参数：
        P_est: (N, 3) 估计轨迹点
        P_gt: (N, 3) 真值轨迹点
    
    返回：
        scale: 尺度因子
        R: (3, 3) 旋转矩阵
        t: (3,) 平移向量
    """
    #1. 去中心化
    mu_est = np.mean(P_est, axis=0)
    mu_gt = np.mean(P_gt, axis=0)
    p_est_centered = P_est - mu_est
    p_gt_centered = P_gt - mu_gt

    #2. 计算协方差矩阵
    W = p_est_centered.T @ p_gt_centered

    #3. SVD 分解
    U, S, Vt = np.linalg.svd(W)

    #4. 计算旋转矩阵
    R = Vt.T @ U.T
    # 处理反射（确保 det(R) = 1）
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T
    
    #5. 计算尺度
    var_est = np.sum(p_est_centered ** 2)
    scale = np.sum(S) / var_est if var_est > 1e-9 else 1.0

    #6. 计算平移
    t = mu_gt - scale * R @ mu_est

    return scale, R, t

def apply_alignment(P: np.ndarray, scale: float, R: np.ndarray, t: np.ndarray) -> np.ndarray:
    """
    应用 Sim(3) 变换
    
    P_aligned = scale * R @ P + t
    """
    return scale * (R @ P.T).T + t

def compute_ATE(P_aligned: np.ndarray, P_gt: np.ndarray) -> float:
    """
    计算 ATE (Position Only)
    
    参数：
        P_est_aligned: (N, 3) 对齐后的估计轨迹点
        P_gt: (N, 3) 真值轨迹点
    返回：
        dict: {rmse, mean, median, max, errors}
    """
    errors = np.linalg.norm(P_aligned - P_gt, axis=1)
    
    return {
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "mean": float(np.mean(errors)),
        "median": float(np.median(errors)),
        "max": float(np.max(errors)),
        "min": float(np.min(errors)),
        "std": float(np.std(errors)),
        "errors": errors  # 保留用于绘图
    }


def plot_trajectories(
    P_est: np.ndarray,
    P_gt: np.ndarray,
    P_aligned: np.ndarray,
    output_path: Path
) -> None:
    """
    绘制轨迹对比图：
    1) XY 对齐前
    2) XY 对齐后
    3) XYZ 三维轨迹
    """
    fig = plt.figure(figsize=(21, 6))

    # 左图：对齐前（XY）
    ax1 = fig.add_subplot(1, 3, 1)
    ax1.plot(P_gt[:, 0], P_gt[:, 1], 'g-', label='Ground Truth', linewidth=2)
    ax1.plot(P_est[:, 0], P_est[:, 1], 'r--', label='Estimated (raw)', linewidth=2, alpha=0.7)
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_title('Before Alignment (XY)')
    ax1.legend()
    ax1.grid(True)
    ax1.axis('equal')

    # 中图：对齐后（XY）
    ax2 = fig.add_subplot(1, 3, 2)
    ax2.plot(P_gt[:, 0], P_gt[:, 1], 'g-', label='Ground Truth', linewidth=2)
    ax2.plot(P_aligned[:, 0], P_aligned[:, 1], 'b--', label='Estimated (aligned)', linewidth=2, alpha=0.7)
    ax2.set_xlabel('X (m)')
    ax2.set_ylabel('Y (m)')
    ax2.set_title('After Sim(3) Alignment (XY)')
    ax2.legend()
    ax2.grid(True)
    ax2.axis('equal')

    # 右图：三维轨迹（XYZ）
    ax3 = fig.add_subplot(1, 3, 3, projection='3d')
    ax3.plot(P_gt[:, 0], P_gt[:, 1], P_gt[:, 2], 'g-', label='Ground Truth', linewidth=2)
    ax3.plot(P_aligned[:, 0], P_aligned[:, 1], P_aligned[:, 2], 'b--', label='Estimated (aligned)', linewidth=2, alpha=0.8)
    ax3.set_xlabel('X (m)')
    ax3.set_ylabel('Y (m)')
    ax3.set_zlabel('Z (m)')
    ax3.set_title('3D Trajectory (XYZ)')
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"✅ 保存轨迹对比图: {output_path}")



def compute_ATE_pipeline(
        traj_est_path: Path, 
        traj_gt_path: Path, 
        output_dir: Path,
    max_time_diff: float = 0.02) -> dict | None:
    """
    计算 ATE (Position Only)
    
    参数：
        traj_est_path: 估计轨迹 CSV 文件路径
        traj_gt_path: 真实轨迹 CSV 文件路径
        output_dir: 结果输出目录
        max_time_diff: 时间戳对齐的最大允许差异（秒）
    

    """
    print("="*80)
    print("ATE 评估 - Position Only")
    print("="*80)
    
    # 1. 加载轨迹
    print(f"\n📂 加载估计轨迹: {traj_est_path}")
    ts_est, pos_est = load_trajectory(traj_est_path)
    print(f"一共{len(ts_est)}位姿点")
    print(f"\n📂 加载真实轨迹: {traj_gt_path}")
    ts_gt, pos_gt = load_trajectory(traj_gt_path)
    print(f"一共{len(ts_gt)}位姿点")

    # 2. 时间戳对齐（最近邻）
    print("\n⏱️ 进行时间戳对齐 (最近邻)")
    matches = associate_timestamps(ts_est, ts_gt, max_time_diff)
    print(f"找到 {len(matches)} 对齐的时间戳")
    if len(matches) < 10:
        print("❌ 错误: 匹配点对太少（< 10），无法进行 ATE 评估")
        return None
    # 提取匹配的位姿点
    est_indices = [m[0] for m in matches]
    gt_indices = [m[1] for m in matches]
    
    P_est_matched = pos_est[est_indices]
    P_gt_matched = pos_gt[gt_indices]
    ts_matched = ts_est[est_indices]

    # 3. sim(3) 对齐（Umeyama 算法）
    print("\n🔧 进行 sim(3) 对齐 (Umeyama 算法)")
    scale, R, t = umeyama_alignment(P_est_matched, P_gt_matched)

    print(f"   尺度 (scale): {scale:.6f}")
    print(f"   旋转矩阵:\n{R}")
    print(f"   平移向量: {t}")
    
    P_aligned = apply_alignment(P_est_matched, scale, R, t)

    # 4. 计算 ATE (Position Only)
    print("\n📏 计算 ATE (Position Only)")
    ate_stats = compute_ATE(P_aligned, P_gt_matched)
    
    print(f"   RMSE:   {ate_stats['rmse']:.6f} m")
    print(f"   Mean:   {ate_stats['mean']:.6f} m")
    print(f"   Median: {ate_stats['median']:.6f} m")
    print(f"   Max:    {ate_stats['max']:.6f} m")
    print(f"   Min:    {ate_stats['min']:.6f} m")
    print(f"   Std:    {ate_stats['std']:.6f} m")

    # 5. 可视化轨迹
    plot_file = output_dir / "trajectory_comparison.png"
    plot_trajectories(P_est_matched, P_gt_matched, P_aligned, plot_file)

    # 6. 保存结果
    output_dir.mkdir(parents=True, exist_ok=True)
    # 保存 summary
    summary = {
        "num_pairs": len(matches),
        "rmse": ate_stats['rmse'],
        "mean": ate_stats['mean'],
        "median": ate_stats['median'],
        "max": ate_stats['max'],
        "min": ate_stats['min'],
        "std": ate_stats['std'],
        "scale": float(scale),
        "timestamp_max_diff": max_time_diff,
        "num_matched_timestamps": int(len(ts_matched))
    }
    
    summary_file = output_dir / "ate_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n✅ 保存 ATE summary: {summary_file}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="计算 ATE 并输出轨迹可视化")
    parser.add_argument("--traj-est", type=Path, default=TRAJ_EST_DIR, help="估计轨迹 CSV 路径")
    parser.add_argument("--traj-gt", type=Path, default=TRAJ_GT_DIR, help="真实轨迹 CSV 路径")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="输出目录")
    parser.add_argument("--max-time-diff", type=float, default=0.02, help="时间戳匹配最大差值（秒）")
    args = parser.parse_args()

    if not args.traj_est.exists():
        raise FileNotFoundError(f"估计轨迹文件不存在: {args.traj_est}")
    if not args.traj_gt.exists():
        raise FileNotFoundError(f"真实轨迹文件不存在: {args.traj_gt}")

    stats = compute_ATE_pipeline(
        traj_est_path=args.traj_est,
        traj_gt_path=args.traj_gt,
        output_dir=args.output_dir,
        max_time_diff=args.max_time_diff,
    )
    if stats is None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
    
'''
python scripts\compute_ATE.py`
 --traj-est [traj_est.csv] `
 --traj-gt [traj_gt.csv] `
 --output-dir runs/tum_freiburg1_desk_baseline_002 `
 --max-time-diff 0.02
'''
