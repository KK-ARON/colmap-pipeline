import subprocess        #调用外部命令
import argparse          #命令行参数解析
from pathlib import Path #路径处理
import time              #time record
import re                #正则表达式

def parse_colmap_logs(stdout_text, stderr_text):
    """
    解析 COLMAP 日志，区分信息性日志和真正的错误
    
    COLMAP 的日志格式: [级别][时间戳 线程ID 源文件:行号] 消息
    级别: I=INFO, E=ERROR标记, W=WARNING
    
    参数：
        stdout_text: 标准输出文本
        stderr_text: 标准错误输出文本
    
    返回：
        tuple: (stdout_clean, stderr_clean)
            stdout_clean: 信息性日志和成功消息
            stderr_clean: 真正的错误消息
    """
    
    if not stderr_text.strip():
        return stdout_text, ""
    
    info_lines = []      # I 级别：信息性日志
    warning_lines = []   # W 级别：警告
    error_lines = []     # E 级别：带"ERROR"关键字的真正错误（非 IMAGE_EXISTS）
    other_lines = []     # 其他行
    
    # 解析日志模式：[级别][时间戳 线程ID 文件:行号] 消息
    log_pattern = r'^([IEW])\d{8}\s+\d{2}:\d{2}:\d{2}\.[\d\s]+\d+\s+[\w.]+:\d+\]\s*(.*)'
    
    for line in stderr_text.split('\n'):
        if not line.strip():
            continue
            
        match = re.match(log_pattern, line)
        if match:
            level = match.group(1)
            message = match.group(2)
            
            if level == 'I':
                # 信息性日志
                info_lines.append(message)
            elif level == 'W':
                # 警告
                warning_lines.append(message)
            elif level == 'E':
                # E 开头的日志中，如果包含"IMAGE_EXISTS"、"Warning"或单纯的信息性内容，视为信息
                # 否则视为错误
                if any(keyword in message for keyword in ['IMAGE_EXISTS', 'Warning', 'Skipping', 'skip']):
                    info_lines.append(f"[提示] {message}")
                else:
                    # 真正的错误：包含 "is not"、"Failed"、"Error" 等关键字
                    if any(keyword in message for keyword in ['is not', 'Failed', 'failed', 'Error', 'error', 'cannot', 'Cannot']):
                        error_lines.append(message)
                    else:
                        info_lines.append(message)
        else:
            # 不符合日志格式的行
            if line.strip():
                other_lines.append(line)
    
    # 构建清理后的输出
    stdout_clean = "\n".join(info_lines)
    if warning_lines:
        if stdout_clean:
            stdout_clean += "\n\n[警告信息]\n"
        else:
            stdout_clean = "[警告信息]\n"
        stdout_clean += "\n".join(warning_lines)
    
    if other_lines:
        if stdout_clean:
            stdout_clean += "\n\n[其他输出]\n"
        else:
            stdout_clean = "[其他输出]\n"
        stdout_clean += "\n".join(other_lines)
    
    stderr_clean = "\n".join(error_lines) if error_lines else ""
    
    return stdout_clean, stderr_clean


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
        # 先解析日志，区分信息性内容和真正的错误
        stdout_clean, stderr_clean = parse_colmap_logs(result.stdout, result.stderr)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"命令: {' '.join(cmd_list)}\n")     #记录执行的命令
            f.write(f"返回码: {result.returncode}\n")    #记录返回码
            f.write(f"超时设置: {timeout} 秒\n\n")       #记录超时设置
            f.write("=" * 60 + "\n")                   
            f.write("标准输出 (STDOUT) - 执行信息\n")    #写入标准输出
            f.write("=" * 60 + "\n")
            f.write(stdout_clean if stdout_clean else "[无输出信息]")
            f.write("\n\n")
            
            if stderr_clean:
                f.write("=" * 60 + "\n")
                f.write("标准错误 (STDERR) - 真正的错误\n")  #写入标准错误
                f.write("=" * 60 + "\n")
                f.write(stderr_clean)
                f.write("\n\n")
            
            f.write("=" * 60 + "\n")
            f.write("原始日志 (调试用)\n")
            f.write("=" * 60 + "\n")
            f.write("[原始 STDOUT]\n")
            f.write(result.stdout if result.stdout else "[空]")#colmap实际不使用result.stdout,所有日志都在result.stderr
            f.write("\n\n[原始 STDERR]\n")
            f.write(result.stderr if result.stderr else "[空]")
            f.write("\n\n")
            f.write("=" * 60 + "\n")
        
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
    """
    执行 COLMAP 特征提取过程

    参数：
        database_path: 数据库文件的路径
        image_path: 图像目录路径
        log_file: 日志文件路径
        camera_model: str，相机模型，默认 "SIMPLE_RADIAL"
        single_camera: bool，是否所有图像共用一个相机，默认 True
        timeout: int，超时时间（秒），默认 None

    返回：
        tuple: (success: bool, elapsed_time: float, error_msg: str)
    """
    cmd_list=[
        "colmap", "feature_extractor",
        "--database_path", str(database_path),
        "--image_path", str(image_path),
        "--ImageReader.camera_model", camera_model,
        "--ImageReader.single_camera", "1" if single_camera else "0"
    ]
    success, elapsed_time, error_msg = run_colmap_command(cmd_list, log_file, timeout)
    return success,elapsed_time,error_msg

def run_feature_matching(database_path, log_file, timeout=None):
    '''
    执行 COLMAP 特征匹配过程
    参数：
        database_path: 数据库文件的路径
        log_file: 日志文件路径
        timeout: int，超时时间（秒），默认 None

    返回：
        tuple: (success: bool, elapsed_time: float, error_msg: str)
    '''
    cmd_list=[
        "colmap", "exhaustive_matcher",
        "--database_path", str(database_path)
    ]
    success, elapsed_time, error_msg = run_colmap_command(cmd_list, log_file, timeout)
    return success,elapsed_time,error_msg

def run_mapper(database_path, image_path, output_path, log_file, timeout=None):
    '''
    执行 COLMAP 稀疏重建过程
    参数：
        database_path: 数据库文件的路径
        image_path: 图像目录路径
        output_path: 输出目录路径
        log_file: 日志文件路径
        timeout: int，超时时间（秒），默认 None
    返回：
        tuple: (success: bool, elapsed_time: float, error_msg: str)
    '''
    cmd_list=[
        "colmap", "mapper",
        "--database_path", str(database_path),
        "--image_path", str(image_path),
        "--output_path", str(output_path)
    ]
    success, elapsed_time, error_msg = run_colmap_command(cmd_list, log_file, timeout)
    return success,elapsed_time,error_msg

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
    pass


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
    
    # 测试 4: 运行 COLMAP 三步流程
    print("\n" + "="*80)
    print("测试 4: COLMAP 三步流程 (特征提取 -> 特征匹配 -> 稀疏重建)")
    print("="*80)
    
    image_dir = Path(r"D:\programs\colmap-pipeline\data\delivery_area\images\dslr_images_undistorted")
    output_dir = Path(r"D:\programs\colmap-pipeline\runs\test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    database_path = output_dir / "database.db"
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"输入图像: {image_dir}")
    print(f"输出目录: {output_dir}\n")
    
    # 步骤 1: 特征提取
    print("步骤 1: 特征提取")
    print("-" * 40)
    success, elapsed, error = run_feature_extraction(
        database_path=database_path,
        image_path=image_dir,
        log_file=log_dir / "feature_extraction.log",
        camera_model="SIMPLE_RADIAL",
        single_camera=True,
        timeout=None
    )
    print(f"成功: {success}, 耗时: {elapsed:.2f}s")
    if error:
        print(f"错误: {error}")
    print()
    
    if success:
        # 步骤 2: 特征匹配
        print("步骤 2: 特征匹配")
        print("-" * 40)
        success, elapsed, error = run_feature_matching(
            database_path=database_path,
            log_file=log_dir / "feature_matching.log",
            timeout=None
        )
        print(f"成功: {success}, 耗时: {elapsed:.2f}s")
        if error:
            print(f"错误: {error}")
        print()
        
        if success:
            # 步骤 3: 稀疏重建
            print("步骤 3: 稀疏重建")
            print("-" * 40)
            sparse_dir = output_dir / "sparse"
            sparse_dir.mkdir(parents=True, exist_ok=True)  # 创建输出目录
            success, elapsed, error = run_mapper(
                database_path=database_path,
                image_path=image_dir,
                output_path=sparse_dir,
                log_file=log_dir / "mapper.log",
                timeout=None
            )
            print(f"成功: {success}, 耗时: {elapsed:.2f}s")
            if error:
                print(f"错误: {error}")
            print()
            
            if success:
                print("="*80)
                print("✓ 所有步骤执行成功！")
                print("="*80)
                print(f"输出结果位置: {output_dir}")
    else:
        print("特征提取失败，停止流程")