#!/usr/bin/env python3
"""
检查 ETH3D 数据集的完整性
"""
from pathlib import Path
import sys

def check_eth3d_dataset(data_dir):
    data_dir = Path(data_dir)
    
    # 检查图像目录
    image_dir = data_dir / "images"/"dslr_images_undistorted"
    if not image_dir.exists():
        print(f"❌ 图像目录不存在: {image_dir}")
        return False
    
    images = list(image_dir.glob("*.JPG")) + list(image_dir.glob("*.jpg"))
    print(f"✅ 找到 {len(images)} 张图像")
    
    if len(images) == 0:
        print("❌ 图像目录为空")
        return False
    
    # 检查第一张图像的分辨率
    try:
        from PIL import Image
        img = Image.open(images[0])
        print(f"✅ 图像分辨率: {img.size[0]} x {img.size[1]}")
    except Exception as e:
        print(f"⚠️  无法读取图像: {e}")
    
    # 检查 groundtruth
    gt_dir = data_dir / "dslr_calibration_undistorted"
    if gt_dir.exists():
        print(f"✅ 找到 groundtruth: {gt_dir}")
        
        cameras_file = gt_dir / "cameras.txt"
        images_file = gt_dir / "images.txt"
        points_file = gt_dir / "points3D.txt"
        
        if cameras_file.exists():
            with open(cameras_file) as f:
                lines = [l for l in f if not l.startswith('#') and l.strip()]
                print(f"   - cameras.txt: {len(lines)} 个相机")
        
        if images_file.exists():
            with open(images_file) as f:
                lines = [l for l in f if not l.startswith('#') and l.strip()]
                # images.txt 每张图像占两行：第一行是图像ID、相机ID、文件名等，第二行是2D特征点和3D点ID
                print(f"   - images.txt: {len(lines)//2} 张注册图像")
        
        if points_file.exists():
            with open(points_file) as f:
                lines = [l for l in f if not l.startswith('#') and l.strip()]
                print(f"   - points3D.txt: {len(lines)} 个3D点")
    else:
        print("⚠️  未找到 groundtruth（正常，可以从头重建）")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/check_data.py data/delivery_area")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    if check_eth3d_dataset(data_dir):
        print("\n✅ 数据集检查通过！")
        sys.exit(0)
    else:
        print("\n❌ 数据集有问题")
        sys.exit(1)