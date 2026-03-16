import json
from pathlib import Path
from add_to_benchmark import add_to_benchmark
from colmap_runner import run_colmap_pipeline
import csv
from compute_ATE import compute_ATE_pipeline
from export_colmap_traj import camera_center, parse_images_txt


# ==================== 本轮可手动修改参数 ====================
DATASET = "ETH3D"
SEQUENCE = "delivery_area"
CONFIG = "baseline"
RUN_ID = "eth3d_delivery_area_baseline_001"
ON_DUPLICATE = "overwrite"   # skip / overwrite / error

CAMERA_MODEL = "SIMPLE_RADIAL"
SINGLE_CAMERA = True
TIMEOUT = None

IMAGE_DIR = Path("data/terrace/images/dslr_images_undistorted")
OUTPUT_DIR = Path("runs/eth3d_terrace_baseline_001")
GT_IMAGES_TXT = IMAGE_DIR.parent.parent / "processed" / "groundtruth" / "images.txt"
ATE_MAX_TIME_DIFF = 1e-6
# ===========================================================


def export_eth3d_matched_trajectories(
    est_images_txt: Path,
    gt_images_txt: Path,
    traj_est_csv: Path,
    traj_gt_csv: Path,
) -> int:
    est_centers = {}
    for name, qw, qx, qy, qz, tx, ty, tz in parse_images_txt(est_images_txt):
        est_centers[name] = camera_center(qw, qx, qy, qz, tx, ty, tz)

    gt_centers = {}
    for name, qw, qx, qy, qz, tx, ty, tz in parse_images_txt(gt_images_txt):
        gt_centers[name] = camera_center(qw, qx, qy, qz, tx, ty, tz)

    common_names = sorted(set(est_centers.keys()) & set(gt_centers.keys()))

    traj_est_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(traj_est_csv, "w", newline="") as f_est, open(traj_gt_csv, "w", newline="") as f_gt:
        writer_est = csv.writer(f_est)
        writer_gt = csv.writer(f_gt)
        writer_est.writerow(["timestamp", "x", "y", "z"])
        writer_gt.writerow(["timestamp", "x", "y", "z"])

        for idx, name in enumerate(common_names):
            timestamp = float(idx)
            c_est = est_centers[name]
            c_gt = gt_centers[name]
            writer_est.writerow([f"{timestamp:.6f}", f"{c_est[0]:.9f}", f"{c_est[1]:.9f}", f"{c_est[2]:.9f}"])
            writer_gt.writerow([f"{timestamp:.6f}", f"{c_gt[0]:.9f}", f"{c_gt[1]:.9f}", f"{c_gt[2]:.9f}"])

    return len(common_names)


def main():
    image_dir = IMAGE_DIR
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("运行 ETH3D ")
    print("=" * 80)
    print(f"输入: {image_dir}")
    print(f"输出: {output_dir}\n")

    result = run_colmap_pipeline(
        image_dir=image_dir,
        output_dir=output_dir,
        camera_model=CAMERA_MODEL,
        single_camera=SINGLE_CAMERA,
        timeout=TIMEOUT
    )

    if result["success"]:
        try:
            est_images_txt = output_dir / "colmap_output" / "sparse" / "0" / "images.txt"
            traj_est = output_dir / "traj_est.csv"
            traj_gt = output_dir / "traj_gt.csv"

            if GT_IMAGES_TXT.exists() and est_images_txt.exists():
                num_pairs = export_eth3d_matched_trajectories(
                    est_images_txt=est_images_txt,
                    gt_images_txt=GT_IMAGES_TXT,
                    traj_est_csv=traj_est,
                    traj_gt_csv=traj_gt,
                )
                print(f"✅ ETH3D 轨迹导出完成，共 {num_pairs} 对同名图像")

                ate_summary = compute_ATE_pipeline(
                    traj_est_path=traj_est,
                    traj_gt_path=traj_gt,
                    output_dir=output_dir,
                    max_time_diff=ATE_MAX_TIME_DIFF,
                )
                if ate_summary is not None:
                    result["ate_rmse"] = ate_summary["rmse"]
                    result["ate_num_pairs"] = ate_summary["num_pairs"]
                    result["ate_scale"] = ate_summary["scale"]
                    print(
                        f"✅ ATE: rmse={result['ate_rmse']:.6f} m, "
                        f"pairs={result['ate_num_pairs']}, scale={result['ate_scale']:.6f}"
                    )
                else:
                    print("⚠️ ETH3D ATE 评估失败，未写入 ATE 指标")
            else:
                print(f"⚠️ 缺少 ATE 输入文件，已跳过 ETH3D ATE: est={est_images_txt.exists()}, gt={GT_IMAGES_TXT.exists()}")
        except Exception as error:
            print(f"⚠️ ETH3D ATE 流程异常，已跳过: {error}")

    summary_file = output_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    benchmark_ok = add_to_benchmark(
        summary_file=summary_file,
        dataset=DATASET,
        sequence=SEQUENCE,
        config=CONFIG,
        run_id=RUN_ID,
        camera_model=CAMERA_MODEL,
        on_duplicate=ON_DUPLICATE,
    )

    print("\n" + "=" * 80)
    print("运行完成！")
    print("=" * 80)
    print(f"Summary: {summary_file}")
    print(f"Benchmark 写入: {'成功' if benchmark_ok else '失败'}")
    if result["success"]:
        print("✅ 重建成功")
        print(f"   输入图像: {result.get('num_images', 'N/A')}")
        print(f"   注册图像: {result['num_registered']}")
        print(f"   注册率: {result['registration_rate']:.2%}")
        print(f"   3D 点数: {result['num_points3d']}")
        print(
            f"   总耗时: {result['time_extraction'] + result['time_matching'] + result['time_mapping']:.2f}s"
        )
        if "ate_rmse" in result:
            print(f"   ATE RMSE: {result['ate_rmse']:.6f} m")
            print(f"   ATE 匹配对: {result['ate_num_pairs']}")
            print(f"   ATE Scale: {result['ate_scale']:.6f}")
    else:
        print(f"❌ 重建失败: {result['error_message']}")


if __name__ == "__main__":
    main()
