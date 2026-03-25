# COLMAP Pipeline

目标：高度自动化的 COLMAP 重建 pipeline，支持从图像序列到稀疏重建、轨迹评估的全流程。

## 已实现功能

### 数据预处理
- **TUM RGB-D 数据集**（`preprocess_tum.py`）：按时间戳排序图像、统一命名为 `000000.png` 序列，并生成 `timestamp_mapping.csv`
- **ETH3D 数据集**（`preprocess_ETH3D.py`）：图像及 groundtruth 的标准化整理

### COLMAP 稀疏重建
- **核心 pipeline 封装**（`colmap_runner.py`）：依次执行特征提取、特征匹配、稀疏重建，自动解析输出模型，支持 CLI 调用
- **自动指标提取**：注册图像数、注册率、三维点数、相机数、各阶段耗时，结果保存为 `summary.json`
- **TUM 一键运行**（`run_tum.py`）：文件顶部可编辑配置块（序列、相机模型、run_id 等），运行后自动写入 benchmark
- **ETH3D 一键运行**（`run_eth3d.py`）：同上，针对 ETH3D 场景

### Benchmark 管理
- **自动汇总**（`add_to_benchmark.py`）：将 `summary.json` 结果追加至 `benchmarks/benchmark_table.csv`
- **去重策略**：基于 `run_id`，支持 `skip` / `overwrite` / `error` 三种模式

### 轨迹导出（ATE 准备）
- **估计轨迹**（`export_colmap_traj.py`）：从 COLMAP `images.txt` 提取相机位置 $C = -R^T \mathbf{t}$，结合 `timestamp_mapping.csv` 生成 `traj_est.csv`
- **真实轨迹**（`export_tum_gt.py`）：从 TUM `groundtruth.txt` 提取位置，生成 `traj_gt.csv`

### ATE 评估（已完成）
- **ATE 计算脚本**（`compute_ATE.py`）：对 `traj_est.csv` 与 `traj_gt.csv` 进行最近邻时间戳匹配（阈值默认 `0.02s`）
- **轨迹对齐方法**：使用 Umeyama 算法求解 Sim(3)（scale + rotation + translation）
- **误差指标输出**：`rmse / mean / median / max / min / std`，保存为 `ate_summary.json`
- **可视化输出**：生成 `trajectory_comparison.png`（对齐前 XY、对齐后 XY、3D 轨迹）

## 预处理后可直接运行的数据目录要求

以下目录结构是运行 `run_tum.py` / `run_eth3d.py` 的输入前提（即执行预处理脚本后的结构）：

### TUM（`preprocess_tum.py` 后）

```
data/
└── TUM-rgb/
    └── prepared/
        └── rgbd_dataset_freiburg1_desk/        # 或 room 等序列
            ├── images/                          # 000000.png, 000001.png, ...
            ├── timestamp_mapping.csv            # frame_id 与原始 timestamp 对应
            └── groundtruth.txt                  # 真实轨迹（用于导出 traj_gt）
```

### ETH3D（`preprocess_ETH3D.py` 后）

```
data/
└── <scene_name>/                                # 例如 delivery_area / terrace
    └── processed/
        ├── images/                              # 预处理后的图像序列
        ├── metadata.json                        # 元数据
        └── groundtruth/
            ├── cameras.txt
            ├── images.txt
            └── points3D.txt
```

只要满足上述结构，即可直接在对应 `run_*.py` 配置里指定序列并运行。

## 快速开始

### 1. 环境配置

```bash
# 克隆仓库
git clone https://github.com/KK-ARON/colmap-pipeline.git
cd colmap-pipeline

# 创建 Conda 环境
conda env create -f environment.yml
conda activate pipeline

# 验证安装
python scripts/check_env.py
```

### 2. TUM 数据集运行示例

```bash
# 1. 预处理（整理图像 + 生成 timestamp_mapping.csv）
python scripts/preprocess_tum.py

# 2. 编辑 run_tum.py 顶部配置块，指定序列、run_id 等参数，然后运行
python scripts/run_tum.py

# 3. 导出轨迹（用于 ATE 评估）
python scripts/export_colmap_traj.py \
    --images_txt  runs/tum_freiburg1_desk/colmap_output/sparse/0/images.txt \
    --ts_mapping  data/TUM-rgb/prepared/rgbd_dataset_freiburg1_desk/timestamp_mapping.csv \
    --output      runs/tum_freiburg1_desk/traj_est.csv

python scripts/export_tum_gt.py \
    --groundtruth  data/TUM-rgb/prepared/rgbd_dataset_freiburg1_desk/groundtruth.txt \
    --output       runs/tum_freiburg1_desk/traj_gt.csv

# 4. 计算 ATE（生成 ate_summary.json 与 trajectory_comparison.png）
python scripts/compute_ATE.py \
    --traj-est      runs/tum_freiburg1_desk/traj_est.csv \
    --traj-gt       runs/tum_freiburg1_desk/traj_gt.csv \
    --output-dir    runs/tum_freiburg1_desk \
    --max-time-diff 0.02
```

## ATE 结果示例（TUM Freiburg1 Room）

来自 `runs/tum_freiburg1_room_baseline_002/ate_summary.json`：

- `num_matched_timestamps`: 1360
- `rmse`: 0.1211 m
- `mean`: 0.0910 m
- `median`: 0.0714 m
- `max`: 0.4373 m
- `std`: 0.0799 m

轨迹对比图（`runs/tum_freiburg1_room_baseline_002/trajectory_comparison.png`）：

![ATE Trajectory Comparison](runs/tum_freiburg1_room_baseline_002/trajectory_comparison.png)

## 项目结构

```
colmap-pipeline/
├── configs/               # 配置文件
├── data/                  # 输入数据（gitignore）
│   ├── TUM-rgb/           # TUM RGB-D 数据集
│   └── delivery_area/     # ETH3D 数据集
├── runs/                  # 输出结果（gitignore）
│   └── <run_name>/
│       ├── summary.json
│       ├── traj_est.csv
│       ├── traj_gt.csv
│       └── colmap_output/
├── benchmarks/            # benchmark CSV 汇总
├── scripts/               # 核心脚本
├── notes/                 # 实验记录
├── environment.yml        # Conda 环境
└── requirements.txt       # Python 依赖
```

## 开发进度

- [x] 环境配置与验证
- [x] TUM / ETH3D 数据预处理
- [x] COLMAP 稀疏重建封装（特征提取、匹配、重建）
- [x] 自动指标提取与 summary.json 输出
- [x] Benchmark CSV 管理（run_id 去重）
- [x] 轨迹导出（traj_est.csv / traj_gt.csv）
- [x] ATE 评估（时间戳匹配 + Umeyama Sim(3) 对齐 + RMSE 指标与轨迹可视化）


## 许可

MIT License