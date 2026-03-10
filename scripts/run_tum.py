from colmap_runner import run_colmap_pipeline
from pathlib import Path
import json
image_dir = Path("data/TUM-rgb/prepared/rgbd_dataset_freiburg1_desk/images")
output_dir = Path("runs/tum_freiburg1_desk")
output_dir.mkdir(parents=True, exist_ok=True)
print("="*80)
print("运行 TUM  -  配置")
print("="*80)
print(f"输入: {image_dir}")
print(f"输出: {output_dir}\n")

result=run_colmap_pipeline(
    image_dir=image_dir,
    output_dir=output_dir,
    camera_model="SIMPLE_RADIAL",
    single_camera=True,
    timeout=None
)
# 保存 summary
summary_file = output_dir / "summary.json"
with open(summary_file, 'w') as f:
    json.dump(result, f, indent=2)

print("\n" + "="*80)
print("运行完成！")
print("="*80)
print(f"Summary: {summary_file}")
if result['success']:
    print(f"✅ 重建成功")
    print(f"   输入图像: {result.get('num_images', 'N/A')}")
    print(f"   注册图像: {result['num_registered']}")
    print(f"   注册率: {result['registration_rate']:.2%}")
    print(f"   3D 点数: {result['num_points3d']}")
    print(f"   总耗时: {result['time_extraction'] + result['time_matching'] + result['time_mapping']:.2f}s")
else:
    print(f"❌ 重建失败: {result['error_message']}")