import subprocess        #调用外部命令
import argparse          #命令行参数解析
from pathlib import Path #路径处理
import time              #time record

def run_colmap_command(cmd_list, log_file, timeout=None):
    """
    执行单个 COLMAP 命令
    
    参数：
        cmd_list: list，命令及参数，例如 ["colmap", "feature_extractor", ...]
        log_file: Path，日志文件路径
        timeout: int，超时时间（秒），None 表示不限制
    
    返回：
        tuple: (success: bool, elapsed_time: float, error_msg: str)
    """    
    start_time = time.time()                           #记录开始时间

    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True) #确保日志目录存在
    
    try:
        #尝试执行命令
        result=subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        #写入日志
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"命令: {' '.join(cmd_list)}\n")     #记录执行的命令
            f.write(f"返回码: {result.returncode}\n")    #记录返回码
            f.write(f"超时设置: {timeout} 秒\n\n")       #记录超时设置
            f.write("=" * 60 + "\n")                   
            f.write("标准输出 (STDOUT)\n")              #写入标准输出
            f.write("=" * 60 + "\n")
            f.write(result.stdout)
            f.write("\n\n")
            f.write("标准错误 (STDERR)\n")              #写入标准错误
            f.write("=" * 60 + "\n")
            f.write(result.stderr)
            f.write("\n\n")
        
        #计算耗时
        elapsed_time = time.time() - start_time #计算耗时
        if result.returncode!=0:
            err_msg=f"命令执行失败，返回码: {result.returncode}"
            return False, elapsed_time, err_msg
        return True, elapsed_time, ""

    #异常：执行超时
    except subprocess.TimeoutExpired:
        elapsed_time=time.time() - start_time
        err_msg=f"命令执行超时，超过最长时限 {timeout} 秒"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"命令: {' '.join(cmd_list)}\n")
            f.write(f"Error: {err_msg}\n")
            f.write("=" * 60 + "\n")
        return False, elapsed_time, err_msg

    #异常：命令未找到
    except FileNotFoundError:
        elapsed_time=0
        err_msg=f"命令未找到，请确保 COLMAP 已正确安装并在系统 PATH 中: {' '.join(cmd_list)}"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"命令: {' '.join(cmd_list)}\n")
            f.write(f"Error: {err_msg}\n")
            f.write("=" * 60 + "\n")
        return False, elapsed_time, err_msg
    
    #异常：其他执行错误
    except Exception as e:
        elapsed_time=time.time() - start_time
        err_msg=f"命令执行出错: {str(e)}"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"命令: {' '.join(cmd_list)}\n")
            f.write(f"Error: {err_msg}\n")
            f.write("=" * 60 + "\n")
        return False, elapsed_time, err_msg


def run_feature_extraction(database_path, image_path, log_file, 
                           camera_model="SIMPLE_RADIAL", 
                           single_camera=True,
                           timeout=None):
    pass

def run_feature_matching(database_path, log_file, timeout=None):
    pass

def run_mapper(database_path, image_path, output_path, log_file, timeout=None):
    pass

def parse_colmap_model(sparse_dir):
    pass

def run_colmap_pipeline(
    image_dir, 
    output_dir,
    camera_model="SIMPLE_RADIAL",  # 默认相机模型
    single_camera=True,            # 默认单相机
    timeout=None                   # 默认无超时        
):
    """
    运行完整的 COLMAP 稀疏重建流程
    
    参数：
        image_dir: 图像目录
        output_dir: 输出目录
        camera_model: 相机模型（SIMPLE_RADIAL/PINHOLE/OPENCV/RADIAL）
        single_camera: 是否所有图像共用一个相机
        timeout: 每个步骤的超时时间（秒），None 表示不限制
    
    返回：
        dict: {
            "success": bool,
            "num_images": int,
            "num_registered": int,
            "num_points3d": int,
            "time_extraction": float,
            "time_matching": float,
            "time_mapping": float,
            "error_message": str
        }
    """
    return result


if __name__ == "__main__":
    # 测试 1: 执行成功的命令
    print("测试 1: colmap -h")
    success, elapsed, error = run_colmap_command(
        ["colmap", "-h"],
        "test_logs/colmap_help.log"
    )
    print(f"  成功: {success}, 耗时: {elapsed:.2f}s, 错误: {error}")
    
    # 测试 2: 不存在的命令
    print("\n测试 2: 不存在的命令")
    success, elapsed, error = run_colmap_command(
        ["not_exist_command"],
        "test_logs/not_exist.log"
    )
    print(f"  成功: {success}, 耗时: {elapsed:.2f}s, 错误: {error}")
    
    # 测试 3: 超时（sleep 5秒，但只给 2秒 timeout）
    print("\n测试 3: 超时测试")
    import sys
    if sys.platform == "win32":
        cmd = ["timeout", "5"]  # Windows
    else:
        cmd = ["sleep", "5"]    # Linux/Mac
    
    success, elapsed, error = run_colmap_command(
        cmd,
        "test_logs/timeout.log",
        timeout=2
    )
    print(f"  成功: {success}, 耗时: {elapsed:.2f}s, 错误: {error}")