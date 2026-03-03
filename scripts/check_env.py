#!/usr/bin/env python3
"""
环境检查脚本：验证所有依赖是否正确安装
"""
import sys
import subprocess
from pathlib import Path

def check_command(cmd, args=["-h"]):
    """检查命令行工具是否可用"""
    try:
        result = subprocess.run(
            [cmd] + args, 
            capture_output=True, 
            text=True,
            timeout=5
        )
        return "✅", result.stdout.split('\n')[0][:60]
    except FileNotFoundError:
        return "❌", "Not found"
    except Exception as e:
        return "⚠️", str(e)[:60]

def check_python_package(pkg_name, import_name=None):
    """检查 Python 包是否可导入"""
    if import_name is None:
        import_name = pkg_name
    try:
        __import__(import_name)
        return "✅"
    except ImportError:
        return "❌"

print("="*70)
print("COLMAP Pipeline 环境检查")
print("="*70)

# 1. Python 环境
print(f"\n[Python 环境]")
print(f"  Python 版本: {sys.version.split()[0]}")
print(f"  可执行文件: {sys.executable}")

# 2. 命令行工具
print(f"\n[命令行工具]")
tools = [
    ("colmap", []),
    ("ffmpeg", ["-version"]),
    ("git", ["--version"]),
]
for tool, args in tools:
    status, info = check_command(tool, args)
    print(f"  {tool:12s}: {status}  {info}")

# 3. Python 核心包
print(f"\n[Python 核心包]")
packages = [
    ("numpy", "numpy"),
    ("opencv-python", "cv2"),
    ("pandas", "pandas"),
    ("matplotlib", "matplotlib"),
    ("pyyaml", "yaml"),
    ("tqdm", "tqdm"),
    ("evo", "evo"),
]
for pkg, import_name in packages:
    status = check_python_package(pkg, import_name)
    print(f"  {pkg:20s}: {status}")

# 4. COLMAP 关键命令
print(f"\n[COLMAP 子命令]")
colmap_cmds = [
    "feature_extractor",
    "exhaustive_matcher",
    "mapper",
    "model_converter",
]
for cmd in colmap_cmds:
    status, _ = check_command("colmap", [cmd, "-h"])
    print(f"  colmap {cmd:20s}: {status}")

print("\n" + "="*70)
if "❌" in str(locals()):
    print("⚠️  发现缺失依赖，请检查上述标记为 ❌ 的项")
    sys.exit(1)
else:
    print("✅ 所有依赖检查通过！")
    sys.exit(0)