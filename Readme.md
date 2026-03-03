# Readme

# COLMAP Pipeline

目标：高度自动化的 COLMAP 重建 pipeline，支持从视频/图像到稀疏/密集重建的全流程。

## 特性

- ✅ 输入标准化（视频转帧 + 时间戳）
- ✅ 一键运行 COLMAP（特征提取/匹配/重建）
- ✅ 自动指标提取（注册率、点数、重投影误差、耗时）
- ✅ TUM 数据集评估（ATE/RPE）
- ✅ 可视化输出（轨迹图、点云）

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

### 2. 运行示例

```bash
# TODO: 添加运行命令
python scripts/run_pipeline.py --input data/example --output runs/example
```

## 项目结构

```
colmap-pipeline/
├── configs/          # 配置文件
├── data/            # 输入数据（gitignore）
├── runs/            # 输出结果（gitignore）
├── scripts/         # 核心脚本
├── notes/           # 实验记录
├── environment.yml  # Conda 环境
├── requirements.txt # Python 依赖
└── README.md
```

## 开发进度

- [x] 环境配置
- [ ] 数据预处理模块
- [ ] COLMAP 封装
- [ ] 指标提取
- [ ] 可视化模块
- [ ] TUM 评估

## 许可

MIT License