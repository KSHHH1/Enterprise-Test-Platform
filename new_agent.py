#!/usr/bin/env python3
"""
企业测试平台 - 独立Agent服务
可独立部署在测试机上，无需依赖enterprise_platform模块
"""
from flask import Flask, jsonify, request
import os
import time
import socket
import subprocess
import json
import threading
import traceback
import logging
from datetime import datetime

# 创建 Flask 应用
app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储正在运行的测试
running_tests = {}

# 停止标志目录
STOP_FLAGS_DIR = os.path.join(os.path.dirname(__file__), 'stop_flags')

def ensure_stop_flags_dir():
    """确保停止标志目录存在"""
    if not os.path.exists(STOP_FLAGS_DIR):
        os.makedirs(STOP_FLAGS_DIR)

def create_stop_flag(test_id):
    """创建停止标志文件"""
    ensure_stop_flags_dir()
    flag_file = os.path.join(STOP_FLAGS_DIR, f"{test_id}.stop")
    with open(flag_file, 'w') as f:
        f.write(str(time.time()))

def remove_stop_flag(test_id):
    """删除停止标志文件"""
    flag_file = os.path.join(STOP_FLAGS_DIR, f"{test_id}.stop")
    if os.path.exists(flag_file):
        try:
            os.remove(flag_file)
        except Exception as e:
            logger.warning(f"删除停止标志文件失败: {e}")

def check_stop_flag(test_id):
    """检查是否存在停止标志"""
    flag_file = os.path.join(STOP_FLAGS_DIR, f"{test_id}.stop")
    return os.path.exists(flag_file)

def safe_import_serial():
    """安全导入serial库"""
    try:
        import serial.tools.list_ports
        return serial.tools.list_ports
    except ImportError:
        return None

def safe_import_psutil():
    """安全导入psutil库"""
    try:
        import psutil
        return psutil
    except ImportError:
        return None

@app.route('/')
def home():
    """主页"""
    return jsonify({
        'message': 'Agent Service is running',
        'status': 'ok',
        'version': '2.0.0'
    })

@app.route('/serials')
@app.route('/api/serials')
def list_serials():
    """获取可用串口列表"""
    try:
        serial_tools = safe_import_serial()
        if not serial_tools:
            return jsonify({
                "success": False, 
                "error": "pyserial库未安装，无法检测串口"
            })
        
        ports = []
        try:
            for p in serial_tools.comports():
                port_info = {
                    "device": p.device,
                    "description": getattr(p, 'description', '未知设备'),
                    "hwid": getattr(p, 'hwid', '未知硬件ID')
                }
                ports.append(port_info)
        except Exception as e:
            logger.error(f"枚举串口时出错: {str(e)}")
        
        # 如果没有找到真实串口，返回空列表或提示信息
        if not ports:
            return jsonify({
                "success": True, 
                "data": [],
                "message": "未检测到可用串口"
            })
        
        return jsonify({"success": True, "data": ports})
    except Exception as e:
        logger.error(f"获取串口列表异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"获取串口时出错: {str(e)}"
        })

@app.route('/cases')
@app.route('/api/cases')
def list_cases():
    """获取测试用例列表"""
    try:
        # 使用与run_case相同的路径优先级
        possible_dirs = [
            # 当前目录下的测试用例（最高优先级）
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_cases')),
            # 测试机统一路径
            r'D:\TEST_CASES',  # 修改为实际的测试机路径
            r'D:\agent\test_cases',
            # 备用路径
            os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_cases')),
            os.path.abspath(os.path.join(os.path.dirname(__file__), '../TEST_CASES')),
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'TEST_CASES')),
            os.path.abspath('test_cases'),
            os.path.abspath('TEST_CASES'),
            os.path.join(os.getcwd(), 'test_cases'),
            os.path.join(os.getcwd(), 'TEST_CASES')
        ]
        
        case_dir = None
        for dir_path in possible_dirs:
            logger.info(f"检查目录: {dir_path}")
            if os.path.exists(dir_path):
                case_dir = dir_path
                logger.info(f"找到测试用例目录: {case_dir}")
                break
        
        if not case_dir:
            logger.warning("未找到测试用例目录，尝试的路径:")
            for dir_path in possible_dirs:
                logger.warning(f"  - {dir_path}")
            
            # 创建更丰富的示例测试用例
            sample_cases = [
                {
                    "name": "basic_test.py",
                    "display_name": "基础串口测试",
                    "path": "示例测试用例 - 基础串口通信测试",
                    "description": "测试串口基本通信功能",
                    "is_sample": True
                },
                {
                    "name": "loopback_test.py", 
                    "display_name": "环回测试",
                    "path": "示例测试用例 - 串口环回测试",
                    "description": "测试串口数据环回功能",
                    "is_sample": True
                },
                {
                    "name": "tk8620_comprehensive_test.py",
                    "display_name": "TK8620综合测试",
                    "path": "示例测试用例 - TK8620模块综合功能测试",
                    "description": "TK8620模块的完整功能测试",
                    "is_sample": True
                },
                {
                    "name": "enhanced_basic_test.py",
                    "display_name": "增强基础测试",
                    "path": "示例测试用例 - 增强版基础测试",
                    "description": "包含更多测试项的基础测试",
                    "is_sample": True
                },
                {
                    "name": "realtime_basic_test.py",
                    "display_name": "实时基础测试",
                    "path": "示例测试用例 - 实时数据测试",
                    "description": "实时数据传输和处理测试",
                    "is_sample": True
                },
                {
                    "name": "test_demo.py",
                    "display_name": "演示测试",
                    "path": "示例测试用例 - 功能演示测试",
                    "description": "用于演示的测试用例",
                    "is_sample": True
                }
            ]
            return jsonify({
                "success": True, 
                "data": sample_cases,
                "message": "未找到测试用例目录，显示示例用例"
            })
        
        cases = []
        for file in os.listdir(case_dir):
            if file.endswith('.py') and not file.startswith('__'):
                case_info = {
                    "name": file,
                    "display_name": file.replace('_', ' ').replace('.py', '').title(),
                    "path": os.path.join(case_dir, file),
                    "description": f"测试用例: {file}",
                    "is_sample": False
                }
                cases.append(case_info)
        
        # 如果找到的测试用例很少，添加一些示例用例（仅当实际测试用例存在时）
        if len(cases) < 3:
            # 检查是否有实际的测试用例文件存在
            actual_test_files = []
            for case_dir in possible_dirs:
                if os.path.exists(case_dir):
                    for file in os.listdir(case_dir):
                        if file.endswith('.py') and not file.startswith('__'):
                            actual_test_files.append(file)
            
            # 只添加实际存在的测试用例作为示例
            sample_cases = []
            if 'tk8620_comprehensive_test.py' in actual_test_files:
                sample_cases.append({
                    "name": "tk8620_comprehensive_test.py",
                    "display_name": "TK8620综合测试",
                    "path": "示例测试用例 - TK8620模块综合功能测试",
                    "description": "TK8620模块的完整功能测试",
                    "is_sample": True
                })
            if 'enhanced_basic_test.py' in actual_test_files:
                sample_cases.append({
                    "name": "enhanced_basic_test.py",
                    "display_name": "增强基础测试",
                    "path": "示例测试用例 - 增强版基础测试",
                    "description": "包含更多测试项的基础测试",
                    "is_sample": True
                })
            
            cases.extend(sample_cases)
        
        logger.info(f"找到测试用例: {len(cases)}个")
        for case in cases:
            logger.info(f"  - {case['name']}")
        return jsonify({"success": True, "data": cases})
    except Exception as e:
        logger.error(f"获取测试用例列表异常: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/run_case', methods=['POST'])
def run_case():
    """启动测试用例"""
    try:
        data = request.json
        case = data.get('case')
        serial_port = data.get('serial')
        
        logger.info(f"收到测试请求: case={case}, serial={serial_port}")
        
        if not case or not serial_port:
            return jsonify({"success": False, "error": "缺少必要参数: case 和 serial"}), 400
        
        # 生成测试ID
        test_id = f"test_{int(time.time())}_{len(running_tests)}"
        
        # 查找真实的测试脚本路径
        possible_dirs = [
            # 当前目录下的测试用例（最高优先级）
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_cases')),
            # 测试机统一路径
            r'D:\TEST_CASES',  # 修改为实际的测试机路径
            r'D:\agent\test_cases',
            # 备用路径
            os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_cases')),
            os.path.abspath(os.path.join(os.path.dirname(__file__), '../TEST_CASES')),
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'TEST_CASES')),
            os.path.abspath('test_cases'),
            os.path.abspath('TEST_CASES'),
            os.path.join(os.getcwd(), 'test_cases'),
            os.path.join(os.getcwd(), 'TEST_CASES')
        ]
        
        script_path = None
        for case_dir in possible_dirs:
            potential_path = os.path.join(case_dir, case)
            logger.info(f"检查脚本路径: {potential_path}")
            if os.path.exists(potential_path):
                script_path = potential_path
                logger.info(f"找到测试脚本: {script_path}")
                break
        
        if not script_path:
            logger.error(f"未找到测试用例: {case}")
            return jsonify({"success": False, "error": f"测试用例不存在: {case}"}), 404
        
        # 初始化测试状态
        test_info = {
            "id": test_id,
            "case": case,
            "serial": serial_port,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "logs": [f"开始执行测试用例: {case}"],
            "result": None
        }
        
        running_tests[test_id] = test_info
        
        # 清除可能存在的停止标志
        remove_stop_flag(test_id)
        
        # 在后台线程中执行测试
        def execute_test():
            try:
                test_info["logs"].append(f"执行脚本: {script_path}")
                test_info["logs"].append(f"使用串口: {serial_port}")
                
                # 执行Python测试脚本
                logger.info(f"执行命令: python {script_path} {serial_port}")
                test_info["logs"].append(f"执行命令: python {script_path} {serial_port}")
                
                # 修改执行方式，使用shell=True并设置正确的工作目录
                script_dir = os.path.dirname(script_path)
                script_name = os.path.basename(script_path)
                
                # 切换到脚本目录执行
                original_cwd = os.getcwd()
                try:
                    os.chdir(script_dir)
                    
                    # 创建进程，实时捕获输出
                    process = subprocess.Popen(
                        f'python "{script_name}" {serial_port} --test-id {test_id} --stop-flags-dir "{STOP_FLAGS_DIR}"',
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=script_dir,
                        bufsize=1,  # 行缓冲
                        universal_newlines=True
                    )
                    
                    # 保存进程引用以便停止
                    test_info["process"] = process
                    
                    test_info["logs"].append("开始实时监控测试输出...")
                    
                    # 用于收集完整输出的变量
                    stdout_lines = []
                    stderr_lines = []
                    log_lock = threading.Lock()  # 创建专用的日志锁
                    
                    def read_stdout():
                        """实时读取标准输出"""
                        try:
                            while True:
                                line = process.stdout.readline()
                                if not line:
                                    break
                                line = line.rstrip('\n\r')
                                if line:
                                    stdout_lines.append(line)
                                    # 实时添加到日志中，使用线程锁保护
                                    with log_lock:
                                        test_info["logs"].append(f"[实时输出] {line}")
                                    logger.info(f"[实时输出] {line}")
                        except Exception as e:
                            with log_lock:
                                test_info["logs"].append(f"读取标准输出异常: {str(e)}")
                        finally:
                            if process.stdout:
                                process.stdout.close()
                    
                    def read_stderr():
                        """实时读取标准错误"""
                        try:
                            while True:
                                line = process.stderr.readline()
                                if not line:
                                    break
                                line = line.rstrip('\n\r')
                                if line:
                                    stderr_lines.append(line)
                                    # 实时添加到日志中，使用线程锁保护
                                    with log_lock:
                                        test_info["logs"].append(f"[错误输出] {line}")
                                    logger.error(f"[错误输出] {line}")
                        except Exception as e:
                            with log_lock:
                                test_info["logs"].append(f"读取标准错误异常: {str(e)}")
                        finally:
                            if process.stderr:
                                process.stderr.close()
                    
                    # 启动读取线程
                    stdout_thread = threading.Thread(target=read_stdout)
                    stderr_thread = threading.Thread(target=read_stderr)
                    stdout_thread.daemon = True
                    stderr_thread.daemon = True
                    stdout_thread.start()
                    stderr_thread.start()
                    
                    # 等待进程完成，最多等待5分钟
                    try:
                        return_code = process.wait(timeout=300)
                    except subprocess.TimeoutExpired:
                        test_info["logs"].append("测试执行超时，正在终止进程...")
                        process.kill()
                        test_info["status"] = "timeout"
                        return
                    
                    # 等待读取线程完成
                    stdout_thread.join(timeout=5)
                    stderr_thread.join(timeout=5)
                    
                    test_info["logs"].append(f"进程执行完成，返回码: {return_code}")
                    
                    # 合并所有输出
                    full_stdout = '\n'.join(stdout_lines)
                    full_stderr = '\n'.join(stderr_lines)
                    
                    if return_code == 0:
                        # 解析测试结果
                        try:
                            # 查找JSON内容（通常以{开始）
                            json_content = None
                            for i, line in enumerate(stdout_lines):
                                if line.strip().startswith('{'):
                                    json_content = '\n'.join(stdout_lines[i:])
                                    break
                            
                            if json_content:
                                test_result = json.loads(json_content)
                                test_info["result"] = test_result
                                test_info["status"] = "completed"
                                test_info["logs"].append(f"测试执行完成，状态: {test_result.get('status', '未知')}")
                            else:
                                test_info["logs"].append("未找到有效的JSON输出")
                                test_info["status"] = "error"
                                
                        except json.JSONDecodeError as e:
                            test_info["logs"].append(f"测试脚本输出格式错误: {str(e)}")
                            test_info["status"] = "error"
                        except Exception as e:
                            test_info["logs"].append(f"解析测试结果异常: {str(e)}")
                            test_info["status"] = "error"
                    else:
                        # 检查是否是因为停止信号导致的退出
                        if test_info["status"] == "stopped":
                            test_info["logs"].append(f"测试因停止信号退出，返回码: {return_code}")
                            # 保持stopped状态，不改变为error
                        elif check_stop_flag(test_id):
                            # 如果存在停止标志文件，说明是正常停止
                            test_info["status"] = "stopped"
                            test_info["logs"].append(f"检测到停止标志，测试正常停止，返回码: {return_code}")
                            remove_stop_flag(test_id)  # 清理停止标志文件
                        else:
                            test_info["logs"].append(f"测试脚本执行失败，返回码: {return_code}")
                            if full_stderr:
                                test_info["logs"].append(f"错误信息: {full_stderr}")
                            test_info["status"] = "error"
                        
                finally:
                    os.chdir(original_cwd)
                    
            except Exception as e:
                test_info["logs"].append(f"执行异常: {str(e)}")
                test_info["logs"].append(f"异常详情: {traceback.format_exc()}")
                test_info["status"] = "error"
            
            test_info["end_time"] = datetime.now().isoformat()
            logger.info(f"测试 {test_id} 执行完成，状态: {test_info['status']}")
        
        # 启动后台线程
        thread = threading.Thread(target=execute_test)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "test_id": test_id,
            "message": "测试已开始执行",
            "status": "running"
        })
    except Exception as e:
        logger.error(f"启动测试异常: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test_status/<test_id>')
def get_test_status(test_id):
    """获取测试状态"""
    if test_id not in running_tests:
        return jsonify({"success": False, "error": "测试ID不存在"}), 404
    
    # 过滤掉不能JSON序列化的字段（如Popen对象）
    test_data = running_tests[test_id].copy()
    if "process" in test_data:
        del test_data["process"]  # 移除Popen对象
    
    return jsonify({"success": True, "data": test_data})

@app.route('/test_logs/<test_id>')
def get_test_logs(test_id):
    """获取测试日志"""
    if test_id not in running_tests:
        return jsonify({"success": False, "error": "测试ID不存在"}), 404
    
    return jsonify({
        "success": True,
        "data": {
            "logs": running_tests[test_id]["logs"],
            "status": running_tests[test_id]["status"]
        }
    })

@app.route('/running_tests')
def list_running_tests():
    """列出所有测试"""
    return jsonify({
        "success": True,
        "data": {
            "all_tests": list(running_tests.keys()),
            "running_count": len([t for t in running_tests.values() if t["status"] == "running"]),
            "total_count": len(running_tests)
        }
    })

@app.route('/stop_test/<test_id>', methods=['POST'])
def stop_test(test_id):
    """停止指定的测试"""
    try:
        if test_id not in running_tests:
            return jsonify({"success": False, "error": f"测试ID不存在: {test_id}"}), 404
        
        test_info = running_tests[test_id]
        
        if test_info["status"] != "running":
            return jsonify({"success": False, "error": f"测试已经停止，当前状态: {test_info['status']}"}), 400
        
        # 更新测试状态
        test_info["status"] = "stopped"
        test_info["end_time"] = datetime.now().isoformat()
        test_info["logs"].append("[WARN] 测试被手动停止")
        
        # 创建停止标志文件，让测试脚本能够检测到
        create_stop_flag(test_id)
        test_info["logs"].append(f"[INFO] 已创建停止标志: {test_id}")
        
        # 如果有进程在运行，尝试终止它
        process_killed = False
        if 'process' in test_info and test_info.get('process'):
            try:
                process = test_info['process']
                
                # 首先尝试优雅终止
                process.terminate()
                test_info["logs"].append("[INFO] 发送终止信号到测试进程")
                
                # 等待进程结束，最多等待3秒
                try:
                    process.wait(timeout=3)
                    test_info["logs"].append("[INFO] 测试进程已优雅终止")
                    process_killed = True
                except subprocess.TimeoutExpired:
                    # 如果进程没有在3秒内结束，强制杀死
                    test_info["logs"].append("[WARN] 进程未响应终止信号，强制杀死进程")
                    process.kill()
                    try:
                        process.wait(timeout=2)
                        test_info["logs"].append("[INFO] 测试进程已强制终止")
                        process_killed = True
                    except subprocess.TimeoutExpired:
                        test_info["logs"].append("[ERROR] 无法终止测试进程")
                
                # 清理进程引用
                test_info['process'] = None
                
            except Exception as e:
                test_info["logs"].append(f"[WARN] 终止进程失败: {str(e)}")
        
        # 如果没有进程引用或进程终止失败，尝试查找并杀死相关进程
        if not process_killed:
            try:
                import psutil
                test_case = test_info.get('case', '')
                test_info["logs"].append(f"[INFO] 尝试查找并终止相关进程: {test_case}")
                
                # 查找所有Python进程
                killed_count = 0
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and 'python' in proc.info['name'].lower():
                            cmdline = proc.info['cmdline']
                            if cmdline and any(test_case in arg for arg in cmdline):
                                test_info["logs"].append(f"[INFO] 找到相关进程 PID {proc.info['pid']}: {' '.join(cmdline)}")
                                proc.terminate()
                                try:
                                    proc.wait(timeout=3)
                                    test_info["logs"].append(f"[INFO] 进程 {proc.info['pid']} 已终止")
                                    killed_count += 1
                                except psutil.TimeoutExpired:
                                    proc.kill()
                                    test_info["logs"].append(f"[INFO] 强制杀死进程 {proc.info['pid']}")
                                    killed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if killed_count > 0:
                    test_info["logs"].append(f"[INFO] 共终止了 {killed_count} 个相关进程")
                else:
                    test_info["logs"].append("[INFO] 未找到相关的测试进程")
                    
            except ImportError:
                test_info["logs"].append("[WARN] psutil模块未安装，无法查找相关进程")
            except Exception as e:
                test_info["logs"].append(f"[WARN] 查找进程失败: {str(e)}")
        
        # 尝试释放可能被占用的串口
        try:
            import serial.tools.list_ports
            import time
            
            # 获取系统中所有串口
            available_ports = [p.device for p in serial.tools.list_ports.comports()]
            test_info["logs"].append(f"[INFO] 检查串口状态，系统可用串口: {available_ports}")
            
            # 强制等待一段时间，让系统释放资源
            time.sleep(2)
            test_info["logs"].append("[INFO] 等待系统释放串口资源")
            
            # 再次检查串口状态
            final_ports = [p.device for p in serial.tools.list_ports.comports()]
            test_info["logs"].append(f"[INFO] 串口释放后状态: {final_ports}")
            
        except Exception as e:
            test_info["logs"].append(f"[WARN] 串口状态检查失败: {str(e)}")
        
        logger.info(f"测试 {test_id} 已被手动停止")
        
        return jsonify({
            "success": True,
            "message": f"测试 {test_id} 已停止",
            "test_status": test_info["status"]
        })
        
    except Exception as e:
        logger.error(f"停止测试失败: {str(e)}")
        return jsonify({"success": False, "error": f"停止测试失败: {str(e)}"}), 500

@app.route('/info')
@app.route('/api/hosts')
def info():
    """获取主机信息"""
    try:
        import platform
        psutil = safe_import_psutil()
        
        # 获取网络接口信息
        network_interfaces = []
        try:
            if psutil:
                for interface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == 2:  # IPv4
                            network_interfaces.append({
                                "interface": interface,
                                "ip": addr.address,
                                "netmask": addr.netmask
                            })
            else:
                # psutil不可用时的备用方案
                try:
                    # 尝试获取本机IP
                    hostname = socket.gethostname()
                    local_ip = socket.gethostbyname(hostname)
                    network_interfaces.append({
                        "interface": "default",
                        "ip": local_ip,
                        "netmask": "255.255.255.0"
                    })
                except:
                    network_interfaces.append({
                        "interface": "localhost",
                        "ip": "127.0.0.1",
                        "netmask": "255.0.0.0"
                    })
        except Exception as e:
            logger.warning(f"获取网络接口信息失败: {str(e)}")
            network_interfaces = [{"interface": "unknown", "ip": "127.0.0.1", "netmask": "255.0.0.0"}]
        
        # 确定测试机位置
        hostname = socket.gethostname()
        location = "未知位置"
        
        # 根据主机名或IP判断位置
        if "test" in hostname.lower() or "测试" in hostname:
            location = "测试机房"
        elif "dev" in hostname.lower() or "开发" in hostname:
            location = "开发环境"
        elif "prod" in hostname.lower() or "生产" in hostname:
            location = "生产环境"
        else:
            # 根据IP段判断位置
            for net_info in network_interfaces:
                ip = net_info["ip"]
                if ip.startswith("192.168.20."):
                    location = "测试机房A区"
                    break
                elif ip.startswith("192.168.21."):
                    location = "测试机房B区"
                    break
                elif ip.startswith("192.168.1."):
                    location = "开发环境"
                    break
                elif ip.startswith("10.8.0."):
                    location = "企业内网测试区"
                    break
            else:
                location = f"测试机 ({hostname})"
        
        # 获取处理器信息
        processor_info = platform.processor()
        if not processor_info:
            # 备用方案获取处理器信息
            try:
                if psutil:
                    processor_info = f"{psutil.cpu_count()} 核心处理器"
                else:
                    processor_info = "未知处理器"
            except:
                processor_info = "未知处理器"
        
        host_info = {
            "hostname": hostname,
            "location": location,
            "ip_addresses": [net["ip"] for net in network_interfaces],
            "network_interfaces": network_interfaces,
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "processor": processor_info,
            "running_tests": len([t for t in running_tests.values() if t["status"] == "running"]),
            "total_tests": len(running_tests),
            "agent_version": "2.0.0",
            "python_version": f"{platform.python_version()}",
            "working_directory": os.getcwd(),
            "script_location": os.path.abspath(__file__),
            "status": "在线",
            "last_update": datetime.now().isoformat(),
            "psutil_available": psutil is not None
        }
        
        return jsonify({
            "success": True,
            "data": [host_info]  # 返回数组格式以兼容前端
        })
    except Exception as e:
        logger.error(f"获取主机信息异常: {str(e)}")
        # 返回基本信息作为备选
        try:
            hostname = socket.gethostname()
            basic_info = {
                "hostname": hostname,
                "location": f"测试机 ({hostname})",
                "ip_addresses": ["127.0.0.1"],
                "running_tests": len([t for t in running_tests.values() if t["status"] == "running"]),
                "total_tests": len(running_tests),
                "agent_version": "2.0.0",
                "python_version": f"{platform.python_version()}",
                "working_directory": os.getcwd(),
                "status": "在线",
                "error": str(e),
                "psutil_available": False
            }
        except Exception as inner_e:
            basic_info = {
                "hostname": "unknown",
                "location": "未知测试机",
                "ip_addresses": ["127.0.0.1"],
                "running_tests": 0,
                "total_tests": 0,
                "agent_version": "2.0.0",
                "status": "在线",
                "error": f"获取信息失败: {str(e)}, {str(inner_e)}",
                "psutil_available": False
            }
        return jsonify({
            "success": True,
            "data": [basic_info]
        })

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        "success": True,
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health')
def api_health():
    """API健康检查（兼容性）"""
    return health()

@app.route('/api/status')
def api_status():
    """API状态检查（兼容性）"""
    return jsonify({
        'status': 'running',
        'service': 'agent',
        'version': '2.0.0'
    })

@app.route('/debug')
def debug_info():
    """调试信息"""
    try:
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(current_dir)
        
        debug_data = {
            "current_file": __file__,
            "current_dir": current_dir,
            "parent_dir": parent_dir,
            "working_dir": os.getcwd(),
            "test_case_paths": [],
            "running_tests": running_tests
        }
        
        # 检查测试用例目录
        possible_dirs = [
            os.path.join(parent_dir, 'test_cases'),
            os.path.join(parent_dir, 'TEST_CASES'),
            os.path.join(current_dir, 'test_cases'),
            os.path.join(current_dir, 'TEST_CASES'),
            'test_cases',
            'TEST_CASES'
        ]
        
        for test_dir in possible_dirs:
            abs_path = os.path.abspath(test_dir)
            debug_data["test_case_paths"].append({
                "path": abs_path,
                "exists": os.path.exists(abs_path),
                "files": os.listdir(abs_path) if os.path.exists(abs_path) else []
            })
        
        return jsonify({"success": True, "data": debug_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def main():
    """主函数"""
    try:
        logger.info("启动独立Agent服务...")
        logger.info(f"工作目录: {os.getcwd()}")
        logger.info(f"脚本位置: {__file__}")
        
        # 检查测试用例目录
        current_dir = os.path.dirname(__file__)
        test_cases_dir = os.path.join(current_dir, 'test_cases')
        logger.info(f"测试用例目录: {test_cases_dir}")
        logger.info(f"目录是否存在: {os.path.exists(test_cases_dir)}")
        
        if os.path.exists(test_cases_dir):
            logger.info("测试用例文件:")
            for file in os.listdir(test_cases_dir):
                if file.endswith('.py'):
                    logger.info(f"  - {file}")
        
        logger.info("Agent服务启动在端口 5001")
        logger.info("服务地址: http://localhost:5001")
        
        # 启动 Flask 服务
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=False
        )
        
    except KeyboardInterrupt:
        logger.info("Agent服务已停止")
    except Exception as e:
        logger.error(f"Agent服务启动失败: {e}")

if __name__ == "__main__":
    main()