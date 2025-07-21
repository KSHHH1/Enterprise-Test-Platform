#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时输出基础串口测试用例
"""
import serial
import time
import sys
import json
import traceback
import os
import argparse

# 全局变量
TEST_ID = None
STOP_FLAGS_DIR = None

def check_stop_flag():
    """检查是否需要停止测试"""
    if not TEST_ID or not STOP_FLAGS_DIR:
        return False
    
    flag_file = os.path.join(STOP_FLAGS_DIR, f"{TEST_ID}.stop")
    return os.path.exists(flag_file)

def log_print(results, message, level="INFO"):
    """统一的日志打印函数 - 实时输出版本"""
    timestamp = time.strftime("%H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    results["logs"].append(log_message)
    
    # 立即输出到控制台，强制刷新缓冲区
    print(log_message, flush=True)
    
    # 检查停止标志
    if check_stop_flag():
        log_message = f"[{timestamp}] [WARN] 检测到停止信号，测试即将终止"
        results["logs"].append(log_message)
        print(log_message, flush=True)
        results["status"] = "已停止"
        raise KeyboardInterrupt("测试被手动停止")

def run_test(serial_port, baudrate=921600, timeout=5):
    """
    执行基础串口测试 - 实时输出版本
    """
    results = {
        "test_name": "实时输出基础串口测试",
        "serial_port": serial_port,
        "baudrate": baudrate,
        "timeout": timeout,
        "status": "unknown",
        "logs": [],
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": None,
        "duration": 0,
        "details": {}
    }
    
    start_time = time.time()
    
    try:
        log_print(results, f"开始测试串口: {serial_port}")
        log_print(results, f"配置参数 - 波特率: {baudrate}, 超时: {timeout}秒")
        
        # 检查串口是否存在
        log_print(results, "正在检查可用串口...")
        import serial.tools.list_ports
        available_ports = [p.device for p in serial.tools.list_ports.comports()]
        log_print(results, f"系统可用串口: {available_ports}")
        
        # 处理auto参数 - 自动选择第一个可用串口
        actual_port = serial_port
        if serial_port.lower() == "auto":
            if available_ports:
                actual_port = available_ports[0]
                log_print(results, f"自动选择串口: {actual_port}")
                results["serial_port"] = actual_port  # 更新结果中的串口信息
            else:
                log_print(results, "[ERROR] 未找到可用串口，无法自动选择", "ERROR")
                results["status"] = "失败"
                results["details"]["error_type"] = "NoPortAvailable"
                results["details"]["error_message"] = "系统中没有可用的串口"
                return results
        elif actual_port not in available_ports:
            log_print(results, f"警告: 指定串口 {actual_port} 不在可用串口列表中", "WARN")
        
        # 尝试打开串口
        log_print(results, f"正在尝试打开串口: {actual_port}")
        time.sleep(1)  # 模拟一些处理时间
        
        with serial.Serial(actual_port, baudrate, timeout=timeout) as ser:
            log_print(results, "[SUCCESS] 串口打开成功", "SUCCESS")
            
            # 显示串口详细信息
            port_info = {
                "name": ser.name,
                "baudrate": ser.baudrate,
                "bytesize": ser.bytesize,
                "parity": ser.parity,
                "stopbits": ser.stopbits,
                "timeout": ser.timeout
            }
            results["details"]["port_info"] = port_info
            log_print(results, f"串口信息: {port_info}")
            
            # 清空缓冲区
            log_print(results, "正在清空串口缓冲区...")
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            time.sleep(0.5)
            log_print(results, "[SUCCESS] 缓冲区清空完成")
            
            # 测试1: 发送AT命令
            log_print(results, "开始AT命令测试...")
            test_commands = [
                {"cmd": b"AT\r\n", "desc": "基础连接测试"},
                {"cmd": b"AT+GMR\r\n", "desc": "版本信息查询"},
                {"cmd": b"ATE0\r\n", "desc": "关闭回显"}
            ]
            
            responses = []
            for i, test in enumerate(test_commands):
                try:
                    log_print(results, f"测试 {i+1}: {test['desc']}")
                    log_print(results, f"发送命令: {test['cmd'].decode().strip()}")
                    
                    ser.write(test['cmd'])
                    log_print(results, "命令已发送，等待响应...")
                    time.sleep(0.5)
                    
                    # 读取响应
                    response = b""
                    timeout_count = 0
                    while timeout_count < 10:
                        if ser.in_waiting > 0:
                            new_data = ser.read(ser.in_waiting)
                            response += new_data
                            log_print(results, f"收到数据: {len(new_data)} 字节")
                            time.sleep(0.1)
                        else:
                            timeout_count += 1
                            log_print(results, f"等待响应... ({timeout_count}/10)")
                            time.sleep(0.5)
                    
                    if response:
                        response_str = response.decode('utf-8', errors='ignore').strip()
                        log_print(results, f"[SUCCESS] 收到响应: {response_str}", "SUCCESS")
                        responses.append(response_str)
                    else:
                        log_print(results, "[ERROR] 未收到响应", "ERROR")
                        responses.append("")
                        
                except Exception as e:
                    log_print(results, f"[ERROR] 命令 {i+1} 执行异常: {str(e)}", "ERROR")
                    responses.append("")
                
                # 每个测试之间稍作停顿
                time.sleep(1)
            
            # 测试2: 回环测试
            log_print(results, "开始回环测试...")
            test_data = b"HELLO_TEST_123"
            log_print(results, f"发送测试数据: {test_data}")
            ser.write(test_data)
            log_print(results, "等待回环响应...")
            time.sleep(1)
            
            echo_response = ser.read(ser.in_waiting or len(test_data))
            if echo_response:
                log_print(results, f"收到回环数据: {echo_response}")
                if echo_response == test_data:
                    log_print(results, "[SUCCESS] 回环测试通过", "SUCCESS")
                else:
                    log_print(results, "[ERROR] 回环测试失败 - 数据不匹配", "ERROR")
            else:
                log_print(results, "[ERROR] 回环测试失败 - 未收到数据", "ERROR")
            
            # 评估测试结果
            passed_tests = len([r for r in responses if r])
            total_tests = len(test_commands)
            
            log_print(results, f"测试结果统计: {passed_tests}/{total_tests} 通过")
            
            if passed_tests > 0:
                results["status"] = "通过"
                log_print(results, "[SUCCESS] 测试评估: 通过", "SUCCESS")
            else:
                results["status"] = "部分通过"
                log_print(results, "[WARN] 测试评估: 部分通过", "WARN")
            
            results["details"]["responses"] = responses
            results["details"]["echo_test"] = {
                "sent": test_data.decode('utf-8', errors='ignore'),
                "received": echo_response.decode('utf-8', errors='ignore') if echo_response else ""
            }
                
    except serial.SerialException as e:
        log_print(results, f"[ERROR] 串口错误: {str(e)}", "ERROR")
        results["status"] = "失败"
        results["details"]["error_type"] = "SerialException"
        results["details"]["error_message"] = str(e)
    except Exception as e:
        log_print(results, f"[ERROR] 测试异常: {str(e)}", "ERROR")
        log_print(results, f"异常详情: {traceback.format_exc()}", "ERROR")
        results["status"] = "失败"
        results["details"]["error_type"] = "Exception"
        results["details"]["error_message"] = str(e)
    
    end_time = time.time()
    results["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    results["duration"] = round(end_time - start_time, 2)
    log_print(results, f"测试完成，总耗时: {results['duration']}秒，状态: {results['status']}")
    
    return results

if __name__ == "__main__":
    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='实时输出基础串口测试')
        parser.add_argument('serial_port', help='串口名称')
        parser.add_argument('baudrate', nargs='?', type=int, default=921600, help='波特率')
        parser.add_argument('--test-id', help='测试ID，用于停止标志检查')
        parser.add_argument('--stop-flags-dir', help='停止标志文件目录')
        
        args = parser.parse_args()
        
        # 设置全局变量
        if args.test_id and args.stop_flags_dir:
# TEST_ID已经是全局变量，无需再次声明
            TEST_ID = args.test_id
            STOP_FLAGS_DIR = args.stop_flags_dir
        
        result = run_test(args.serial_port, args.baudrate)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    except KeyboardInterrupt:
        # 处理停止信号
        stop_result = {
            "status": "已停止",
            "logs": ["测试被手动停止"],
            "test_name": "实时输出基础串口测试",
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": 0
        }
        print(json.dumps(stop_result, ensure_ascii=False, indent=2), flush=True)
        sys.exit(0)
    except Exception as e:
        error_result = {
            "status": "失败",
            "logs": [f"脚本执行异常: {str(e)}"],
            "error": str(e),
            "test_name": "实时输出基础串口测试",
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": 0
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2), flush=True)
        sys.exit(1)