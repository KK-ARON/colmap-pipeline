import sys
from pathlib import Path
import time

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from colmap_runner import run_feature_extraction, run_feature_matching, run_mapper

def main():
    # 配置路径
    image_dir = Path(r"D:\programs\colmap-pipeline\data\delivery_area\images\dslr_images_undistorted")
    output_dir = Path(r"D:\programs\colmap-pipeline\runs\test")
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 数据库文件路径
    database_path = output_dir / "database.db"
    
    # 日志目录
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("COLMAP 三步流程测试")
    print("=" * 80)
    print(f"输入图像目录: {image_dir}")
    print(f"输出目录: {output_dir}")
    print(f"数据库文件: {database_path}")
    print()
    
    # 检查图像目录是否存在
    if not image_dir.exists():
        print(f"错误: 图像目录不存在: {image_dir}")
        return
    
    images = list(image_dir.glob("*.*"))
    print(f"找到 {len(images)} 张图像\n")
    
    results = {
        "feature_extraction": None,
        "feature_matching": None,
        "mapper": None
    }
    
    # 步骤 1: 特征提取
    print("=" * 80)
    print("步骤 1: 特征提取")
    print("=" * 80)
    start_time = time.time()
    success, elapsed, error = run_feature_extraction(
        database_path=database_path,
        image_path=image_dir,
        log_file=log_dir / "feature_extraction.log",
        camera_model="SIMPLE_RADIAL",
        single_camera=True,
        timeout=None
    )
    results["feature_extraction"] = {
        "success": success,
        "elapsed_time": elapsed,
        "error": error
    }
    print(f"成功: {success}")
    print(f"耗时: {elapsed:.2f} 秒")
    if error:
        print(f"错误信息: {error}")
    print()
    
    if not success:
        print("特征提取失败，程序中止")
        print_summary(results)
        return
    
    # 步骤 2: 特征匹配
    print("=" * 80)
    print("步骤 2: 特征匹配")
    print("=" * 80)
    success, elapsed, error = run_feature_matching(
        database_path=database_path,
        log_file=log_dir / "feature_matching.log",
        timeout=None
    )
    results["feature_matching"] = {
        "success": success,
        "elapsed_time": elapsed,
        "error": error
    }
    print(f"成功: {success}")
    print(f"耗时: {elapsed:.2f} 秒")
    if error:
        print(f"错误信息: {error}")
    print()
    
    if not success:
        print("特征匹配失败，程序中止")
        print_summary(results)
        return
    
    # 步骤 3: 稀疏重建
    print("=" * 80)
    print("步骤 3: 稀疏重建 (Mapper)")
    print("=" * 80)
    success, elapsed, error = run_mapper(
        database_path=database_path,
        image_path=image_dir,
        output_path=output_dir / "sparse",
        log_file=log_dir / "mapper.log",
        timeout=None
    )
    results["mapper"] = {
        "success": success,
        "elapsed_time": elapsed,
        "error": error
    }
    print(f"成功: {success}")
    print(f"耗时: {elapsed:.2f} 秒")
    if error:
        print(f"错误信息: {error}")
    print()
    
    # 打印总结
    print_summary(results)
    
    # 检查输出文件
    print("=" * 80)
    print("输出文件总览")
    print("=" * 80)
    print(f"输出目录: {output_dir}")
    if output_dir.exists():
        for item in sorted(output_dir.rglob("*")):
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"  {item.relative_to(output_dir)} ({size_mb:.2f} MB)")
    print()

def print_summary(results):
    print("=" * 80)
    print("执行总结")
    print("=" * 80)
    for step, result in results.items():
        if result is None:
            print(f"{step}: 未执行")
        else:
            status = "✓ 成功" if result["success"] else "✗ 失败"
            print(f"{step}: {status} (耗时: {result['elapsed_time']:.2f}s)")
            if result["error"]:
                print(f"  错误: {result['error']}")
    print()

if __name__ == "__main__":
    main()
