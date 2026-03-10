#!/usr/bin/env python3
"""
数据预处理：将 ETH3D 数据集转为标准格式
"""
import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime

def preprocess_eth3d(input_dir, output_dir):
    """
    处理 ETH3D 数据集
    
    输入：
      data/delivery_area/
        ├── images/
        └── dslr_calibration_undistorted/  (可选)
    
    输出：
      data/delivery_area/processed/
        ├── images/  (软链接或复制)
        ├── groundtruth/  (如果有)
        └── metadata.json
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 处理图像
    input_images = input_dir / "images"/"dslr_images_undistorted"
    output_images = output_dir / "images"
    
    if not input_images.exists():
        raise FileNotFoundError(f"图像目录不存在: {input_images}")
    
    print(f"📁 处理图像目录...")
    
    # 创建软链接（Windows 需要管理员权限，否则用复制）
    if output_images.exists():
        shutil.rmtree(output_images)
    
    try:
        output_images.symlink_to(input_images.resolve(), target_is_directory=True)
        print(f"   ✅ 创建软链接: {output_images} -> {input_images}")
    except OSError:
        # Windows 无管理员权限时，改用复制
        shutil.copytree(input_images, output_images)
        print(f"   ✅ 复制图像到: {output_images}")
    
    # 统计图像
    images = list(output_images.glob("*.JPG")) + list(output_images.glob("*.jpg"))
    images = sorted(images)
    print(f"   找到 {len(images)} 张图像")
    
    # 2. 处理 groundtruth（如果存在）
    input_gt = input_dir / "gt"
    if input_gt.exists():
        output_gt = output_dir / "groundtruth"
        output_gt.mkdir(exist_ok=True)
        
        print(f"📁 复制 groundtruth...")
        for file in ["cameras.txt", "images.txt", "points3D.txt"]:
            src = input_gt / file
            dst = output_gt / file
            if src.exists():
                shutil.copy2(src, dst)
                print(f"   ✅ {file}")
    
    # 3. 生成元信息
    metadata = {
        "scene_name": input_dir.name,
        "source": "ETH3D",
        "num_images": len(images),
        "processed_at": datetime.now().isoformat(),
        "image_dir": str(output_images.relative_to(output_dir)),
        "has_groundtruth": input_gt.exists(),
    }
    
    # 读取第一张图像的分辨率
    try:
        from PIL import Image
        img = Image.open(images[0])
        metadata["image_width"] = img.size[0]
        metadata["image_height"] = img.size[1]
    except:
        pass
    
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ 预处理完成！")
    print(f"   输出目录: {output_dir}")
    print(f"   元信息: {metadata_file}")
    
    return metadata

def main():
    parser = argparse.ArgumentParser(description="预处理 ETH3D 数据集")
    parser.add_argument("--input", required=True, help="输入目录（例如 data/delivery_area）")
    parser.add_argument("--output", help="输出目录（默认为 input/processed）")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output) if args.output else input_dir / "processed"
    
    preprocess_eth3d(input_dir, output_dir)

if __name__ == "__main__":
    main()
# 2. 预处理
# python scripts/preprocess.py --input data/delivery_area