"""
企业测试平台 - Agent核心模块
"""
import os
import subprocess
import threading
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...config import get_config
from ...utils import get_logger, SerialUtils, FileUtils, JsonFileManager
from ...models import SerialPort, TestCase, TestResult, TestStatus, ApiResponse

class AgentCore:
    """Agent核心类"""
    
    def __init__(self, config_name: str = None):
        self.config = get_config(config_name)
        self.logger = get_logger('enterprise_platform.agent')
        self.file_utils = FileUtils(config_name)
        
        # 手动配置的主机管理器
        self.manual_hosts_manager = JsonFileManager(self.config.MANUAL_HOSTS_FILE)
        
        # 运行中的测试
        self.running_tests: Dict[str, TestResult] = {}
        self.test_lock = threading.Lock()
        
        self.logger.info("Agent核心模块初始化完成")
    
    def get_serial_ports(self) -> List[SerialPort]:
        """获取串口列表"""
        try:
            ports_data = SerialUtils.list_serial_ports()
            ports = [SerialPort(**port_data) for port_data in ports_data]
            self.logger.info(f"获取到 {len(ports)} 个串口")
            return ports
        except Exception as e:
            self.logger.error(f"获取串口列表失败: {e}")
            return []
    
    def get_test_cases(self) -> List[TestCase]:
        """获取测试用例列表"""
        try:
            cases_data = self.file_utils.list_test_cases()
            cases = [TestCase(**case_data) for case_data in cases_data]
            self.logger.info(f"获取到 {len(cases)} 个测试用例")
            return cases
        except Exception as e:
            self.logger.error(f"获取测试用例列表失败: {e}")
            return []
    
    def get_manual_hosts(self) -> List[str]:
        """获取手动配置的主机列表"""
        try:
            hosts_data = self.manual_hosts_manager.load([])
            hosts = [host_info.get('ip', host_info) if isinstance(host_info, dict) else host_info 
                    for host_info in hosts_data]
            self.logger.info(f"获取到 {len(hosts)} 个手动配置的主机")
            return hosts
        except Exception as e:
            self.logger.error(f"获取手动配置主机失败: {e}")
            return []
    
    def run_test_case(self, case_name: str, serial_port: str) -> ApiResponse:
        """运行测试用例"""
        try:
            # 生成测试ID
            test_id = f"test_{int(time.time())}_{case_name}_{serial_port}"
            
            # 查找测试用例路径
            case_path = self.file_utils.find_test_case_path(case_name)
            if not case_path:
                return ApiResponse(
                    success=False,
                    message=f"测试用例不存在: {case_name}",
                    error_code="CASE_NOT_FOUND"
                )
            
            # 验证串口
            if not SerialUtils.validate_port(serial_port):
                return ApiResponse(
                    success=False,
                    message=f"无效的串口: {serial_port}",
                    error_code="INVALID_PORT"
                )
            
            # 创建测试结果对象
            test_result = TestResult(
                test_id=test_id,
                host_ip="127.0.0.1",  # Agent本地IP
                case_name=case_name,
                serial_port=serial_port,
                status=TestStatus.PENDING,
                start_time=datetime.now()
            )
            
            # 添加到运行中的测试
            with self.test_lock:
                self.running_tests[test_id] = test_result
            
            # 启动测试线程
            test_thread = threading.Thread(
                target=self._execute_test,
                args=(test_id, case_path, serial_port),
                daemon=True
            )
            test_thread.start()
            
            self.logger.info(f"测试已启动: {test_id}")
            return ApiResponse(
                success=True,
                data={"test_id": test_id},
                message="测试已启动"
            )
            
        except Exception as e:
            self.logger.error(f"启动测试失败: {e}")
            return ApiResponse(
                success=False,
                message=f"启动测试失败: {str(e)}",
                error_code="TEST_START_ERROR"
            )
    
    def _execute_test(self, test_id: str, case_path: str, serial_port: str):
        """执行测试用例"""
        try:
            with self.test_lock:
                if test_id in self.running_tests:
                    self.running_tests[test_id].status = TestStatus.RUNNING
            
            self.logger.info(f"开始执行测试: {test_id}")
            
            # 构建命令
            cmd = [
                'python', case_path,
                '--port', serial_port,
                '--test-id', test_id
            ]
            
            # 执行测试
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(case_path)
            )
            
            stdout, stderr = process.communicate(timeout=self.config.TEST_TIMEOUT)
            
            # 更新测试结果
            with self.test_lock:
                if test_id in self.running_tests:
                    test_result = self.running_tests[test_id]
                    test_result.end_time = datetime.now()
                    test_result.output = stdout
                    test_result.error = stderr
                    
                    if process.returncode == 0:
                        test_result.status = TestStatus.SUCCESS
                        self.logger.info(f"测试成功: {test_id}")
                    else:
                        test_result.status = TestStatus.FAILED
                        self.logger.warning(f"测试失败: {test_id}, 返回码: {process.returncode}")
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"测试超时: {test_id}")
            with self.test_lock:
                if test_id in self.running_tests:
                    self.running_tests[test_id].status = TestStatus.FAILED
                    self.running_tests[test_id].error = "测试执行超时"
                    self.running_tests[test_id].end_time = datetime.now()
        
        except Exception as e:
            self.logger.error(f"执行测试异常: {test_id}, {e}")
            with self.test_lock:
                if test_id in self.running_tests:
                    self.running_tests[test_id].status = TestStatus.FAILED
                    self.running_tests[test_id].error = f"执行异常: {str(e)}"
                    self.running_tests[test_id].end_time = datetime.now()
    
    def get_test_result(self, test_id: str) -> Optional[TestResult]:
        """获取测试结果"""
        with self.test_lock:
            return self.running_tests.get(test_id)
    
    def get_running_tests(self) -> List[TestResult]:
        """获取所有运行中的测试"""
        with self.test_lock:
            return list(self.running_tests.values())
    
    def cancel_test(self, test_id: str) -> ApiResponse:
        """取消测试"""
        try:
            with self.test_lock:
                if test_id not in self.running_tests:
                    return ApiResponse(
                        success=False,
                        message=f"测试不存在: {test_id}",
                        error_code="TEST_NOT_FOUND"
                    )
                
                test_result = self.running_tests[test_id]
                if test_result.status in [TestStatus.SUCCESS, TestStatus.FAILED, TestStatus.CANCELLED]:
                    return ApiResponse(
                        success=False,
                        message=f"测试已结束，无法取消: {test_id}",
                        error_code="TEST_ALREADY_FINISHED"
                    )
                
                test_result.status = TestStatus.CANCELLED
                test_result.end_time = datetime.now()
                test_result.error = "用户取消"
            
            self.logger.info(f"测试已取消: {test_id}")
            return ApiResponse(
                success=True,
                message="测试已取消"
            )
            
        except Exception as e:
            self.logger.error(f"取消测试失败: {e}")
            return ApiResponse(
                success=False,
                message=f"取消测试失败: {str(e)}",
                error_code="CANCEL_ERROR"
            )