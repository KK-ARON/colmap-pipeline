import json
from pathlib import Path
from add_to_benchmark import add_to_benchmark
from colmap_runner import run_colmap_pipeline


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
# ===========================================================


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
    else:
        print(f"❌ 重建失败: {result['error_message']}")


if __name__ == "__main__":
    main()
