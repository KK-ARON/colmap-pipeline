from pathlib import Path
import shutil
import argparse
def prepare_tum(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # 1. 读取 rgb.txt
    rgb_txt = input_dir / "rgb.txt"
    image_list = []  # [(timestamp, filename), ...]
    
    with open(rgb_txt, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split()
            timestamp = float(parts[0])
            filename = parts[1]
            image_list.append((timestamp, filename))
    # 2. 按时间戳排序
    image_list.sort(key=lambda x: x[0])  
    # 3. 创建输出目录
    output_image = output_dir / "images"
    output_image.mkdir(parents=True, exist_ok=True)
    # 4. 复制图像并重命名
    mapping=[]
    for i, (timestamp, filename) in enumerate(image_list):
        src = input_dir / filename
        dst = output_image / f"{i:06d}.png"
        #复制文件
        shutil.copy2(src, dst) 
        #记录映射关系
        mapping.append((dst.name,timestamp))
    # 5. 保存映射关系
    mapping_file = output_dir / "timestamp_mapping.csv"
    with open(mapping_file, 'w') as f:
        f.write("filename,timestamp\n")
        for filename, timestamp in mapping:
            f.write(f"{filename},{timestamp}\n")
    # 6. 复制 groundtruth.txt（备用）
    gt_src = input_dir / "groundtruth.txt"
    if gt_src.exists():
        shutil.copy2(gt_src, output_dir / "groundtruth.txt")
    
    print(f"✅ 处理完成！")
    print(f"   总图像数: {len(image_list)}")
    print(f"   输出目录: {output_dir}")
    print(f"   图像目录: {output_image}")
    print(f"   映射文件: {mapping_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="准备 TUM 数据集")
    parser.add_argument("--input", required=True, help="TUM 原始数据目录")
    parser.add_argument("--output", required=True, help="输出目录")
    args = parser.parse_args()
    prepare_tum(args.input, args.output)

# 使用示例:
'''
# PowerShell:
python scripts/preprocess_tum.py --input data/TUM-rgb/rgbd_dataset_freiburg1_room --output data/TUM-rgb/prepared/rgbd_dataset_freiburg1_room

# PowerShell（多行）:
python scripts/prepare_tum.py `
    --input data/TUM-rgb/rgbd_dataset_freiburg1_desk `
    --output data/TUM-rgb/prepared/rgbd_dataset_freiburg1_desk

# Bash / Linux / macOS:
python scripts/prepare_tum.py \
    --input data/TUM-rgb/rgbd_dataset_freiburg1_desk \
    --output data/TUM-rgb/prepared/rgbd_dataset_freiburg1_desk
'''
