import json
from pathlib import Path
import csv
from datetime import datetime
import argparse


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_FIELDS = [
    "dataset",
    "sequence",
    "config",
    "num_images_input",
    "num_registered",
    "registration_rate",
    "num_points3d",
    "time_extraction_s",
    "time_matching_s",
    "time_mapping_s",
    "time_total_s",
    "camera_model",
    "status",
    "run_id",
    "timestamp",
]


def load_existing_records(benchmark_file):
    if not benchmark_file.exists():
        return []

    with open(benchmark_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_records(benchmark_file, records):
    with open(benchmark_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=BENCHMARK_FIELDS)
        writer.writeheader()
        writer.writerows(records)


def add_to_benchmark(summary_file, dataset, sequence, config, run_id,
                     camera_model="SIMPLE_RADIAL", on_duplicate="overwrite"):
    """
    将 summary.json 的结果添加到 benchmark_table.csv
    
    参数：
        summary_file: summary.json 文件路径
        dataset: 数据集名称（例如 TUM）
        sequence: 序列名称（例如 freiburg1_desk）
        config: 配置名称（例如 baseline）
        run_id: 运行 ID（例如 baseline_001）
        camera_model: 相机模型（默认 SIMPLE_RADIAL）
        on_duplicate: 重复 run_id 的处理策略（skip/overwrite/error）
    """

    # 1. 读取 summary.json
    summary_file = Path(summary_file)
    if not summary_file.exists():
        print(f"❌ 错误: summary.json 不存在: {summary_file}")
        return False

    try:
        with open(summary_file, "r", encoding="utf-8") as f:
            result = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ 错误: summary.json 不是有效的 JSON: {summary_file}")
        print(f"   详情: {e}")
        return False

    time_extraction = float(result.get("time_extraction", 0) or 0)
    time_matching = float(result.get("time_matching", 0) or 0)
    time_mapping = float(result.get("time_mapping", 0) or 0)
    camera_model_value = result.get("camera_model", camera_model)
    
   
    # 2. 准备记录
    record = {
        "dataset": dataset,
        "sequence": sequence,
        "config": config,
        "num_images_input": result.get("num_images", 0),
        "num_registered": result.get("num_registered", 0),
        "registration_rate": f"{result.get('registration_rate', 0):.4f}",
        "num_points3d": result.get("num_points3d", 0),
        "time_extraction_s": f"{time_extraction:.2f}",
        "time_matching_s": f"{time_matching:.2f}",
        "time_mapping_s": f"{time_mapping:.2f}",
        "time_total_s": f"{time_extraction + time_matching + time_mapping:.2f}",
        "camera_model": camera_model_value,
        "status": "success" if result.get("success", False) else "failed",
        "run_id": run_id,
        "timestamp": datetime.now().isoformat()
    }

    # 3. benchmark 文件路径
    benchmark_file = REPO_ROOT / "benchmarks" / "benchmark_table.csv"
    benchmark_file.parent.mkdir(parents=True, exist_ok=True)

    # 4. 处理重复 run_id
    existing_records = load_existing_records(benchmark_file)
    duplicate_index = next(
        (index for index, row in enumerate(existing_records) if row.get("run_id") == run_id),
        None
    )

    if duplicate_index is not None:
        if on_duplicate == "skip":
            print(f"⚠️ 检测到重复 run_id，已跳过: {run_id}")
            return True
        if on_duplicate == "error":
            print(f"❌ 错误: benchmark 中已存在相同 run_id: {run_id}")
            return False

        existing_records[duplicate_index] = record
        save_records(benchmark_file, existing_records)
        print(f"♻️ 已覆盖 benchmark 记录: {benchmark_file}")
    else:
        existing_records.append(record)
        save_records(benchmark_file, existing_records)
        print(f"✅ 已添加到 benchmark 表: {benchmark_file}")

    print(f"   数据集: {dataset}/{sequence}")
    print(f"   配置: {config}")
    print(f"   状态: {record['status']}")
    print(f"   注册率: {float(record['registration_rate']):.2%}")
      
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="添加结果到 benchmark 表")
    parser.add_argument("--summary", required=True, help="summary.json 文件路径")
    parser.add_argument("--dataset", required=True, help="数据集名称（例如 TUM）")
    parser.add_argument("--sequence", required=True, help="序列名称（例如 freiburg1_desk）")
    parser.add_argument("--config", required=True, help="配置名称（例如 baseline）")
    parser.add_argument("--run_id", required=True, help="运行 ID（例如 baseline_001）")
    parser.add_argument("--camera_model", default="SIMPLE_RADIAL", help="相机模型")
    parser.add_argument(
        "--on_duplicate",
        choices=["skip", "overwrite", "error"],
        default="overwrite",
        help="重复 run_id 时的处理策略"
    )
    
    args = parser.parse_args()
    
    add_to_benchmark(
        summary_file=args.summary,
        dataset=args.dataset,
        sequence=args.sequence,
        config=args.config,
        run_id=args.run_id,
        camera_model=args.camera_model,
        on_duplicate=args.on_duplicate
    )