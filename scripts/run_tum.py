import json
from pathlib import Path
from add_to_benchmark import add_to_benchmark
from colmap_runner import run_colmap_pipeline
from compute_ATE import compute_ATE_pipeline
from export_colmap_traj import export_trajectory
from export_tum_gt import export_groundtruth


# ==================== 本轮可手动修改参数 ====================
DATASET = "TUM"
SEQUENCE = "freiburg1_room"
CONFIG = "baseline"
RUN_ID = "tum_freiburg1_room_baseline_002"
ON_DUPLICATE = "overwrite"   # skip / overwrite / error

CAMERA_MODEL = "SIMPLE_RADIAL"
SINGLE_CAMERA = True
TIMEOUT = None

IMAGE_DIR = Path("data/TUM-rgb/prepared/rgbd_dataset_freiburg1_room/images")
OUTPUT_DIR = Path("runs/tum_freiburg1_room_baseline_002")
TS_MAPPING_CSV = IMAGE_DIR.parent / "timestamp_mapping.csv"
GT_TXT = IMAGE_DIR.parent / "groundtruth.txt"
ATE_MAX_TIME_DIFF = 0.02
# ===========================================================


def main():
    output_dir = OUTPUT_DIR
    image_dir = IMAGE_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("运行 TUM  -  配置")
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
            images_txt = output_dir / "colmap_output" / "sparse" / "0" / "images.txt"
            traj_est = output_dir / "traj_est.csv"
            traj_gt = output_dir / "traj_gt.csv"

            export_trajectory(
                images_txt=images_txt,
                ts_mapping_csv=TS_MAPPING_CSV,
                output_csv=traj_est,
            )
            export_groundtruth(
                groundtruth_txt=GT_TXT,
                output_csv=traj_gt,
            )

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
                print("⚠️ ATE 评估失败，未写入 ATE 指标")
        except Exception as error:
            print(f"⚠️ ATE 流程异常，已跳过: {error}")

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
        print(f"   总耗时: {result['time_extraction'] + result['time_matching'] + result['time_mapping']:.2f}s")
        if "ate_rmse" in result:
            print(f"   ATE RMSE: {result['ate_rmse']:.6f} m")
            print(f"   ATE 匹配对: {result['ate_num_pairs']}")
            print(f"   ATE Scale: {result['ate_scale']:.6f}")
    else:
        print(f"❌ 重建失败: {result['error_message']}")


if __name__ == "__main__":
    main()