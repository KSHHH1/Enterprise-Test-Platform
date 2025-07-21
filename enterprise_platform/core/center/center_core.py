"""
企业测试平台 - Center核心模块
"""
import os
import json
import requests
import threading
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ...config import get_config
from ...utils import get_logger, NetworkUtils
from ...models import Host, HostStatus, SerialPort, TestCase, TestResult, ApiResponse

class CenterCore:
    """Center核心类"""
    
    def __init__(self, config_name: str = None):
        self.config = get_config()
        self.logger = get_logger('enterprise_platform.center')
        self.network_utils = NetworkUtils()  # 创建NetworkUtils实例
        
        # 主机缓存
        self.hosts_cache: Dict[str, Host] = {}
        self.cache_lock = threading.Lock()
        
        # 启动后台任务
        self._start_background_tasks()
        
        self.logger.info("Center核心模块初始化完成")
    
    def _start_background_tasks(self):
        """启动后台任务"""
        # 主机发现任务
        discovery_thread = threading.Thread(
            target=self._host_discovery_loop,
            daemon=True
        )
        discovery_thread.start()
        
        # 主机状态检查任务
        health_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True
        )
        health_thread.start()
        
        self.logger.info("后台任务已启动")
    
    def _host_discovery_loop(self):
        """主机发现循环"""
        while True:
            try:
                self._discover_hosts()
                time.sleep(self.config.HOST_DISCOVERY_INTERVAL)
            except Exception as e:
                self.logger.error(f"主机发现异常: {e}")
                time.sleep(30)  # 出错时等待30秒
    
    def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                self._check_hosts_health()
                time.sleep(self.config.HEALTH_CHECK_INTERVAL)
            except Exception as e:
                self.logger.error(f"健康检查异常: {e}")
                time.sleep(30)  # 出错时等待30秒
    
    def _discover_hosts(self):
        """发现主机"""
        try:
            # 获取手动配置的主机
            manual_hosts = self._get_manual_hosts()
            
            # 自动发现网络中的主机
            discovered_agents = self.network_utils.discover_agents()
            discovered_hosts = [agent['ip'] for agent in discovered_agents]
            
            # 合并主机列表
            all_hosts = set(manual_hosts + discovered_hosts)
            
            # 更新主机缓存
            with self.cache_lock:
                for host_ip in all_hosts:
                    if host_ip not in self.hosts_cache:
                        host = Host(ip=host_ip, name=f"主机-{host_ip}")
                        self.hosts_cache[host_ip] = host
                        self.logger.info(f"发现新主机: {host_ip}")
            
            self.logger.debug(f"主机发现完成，共 {len(all_hosts)} 台主机")
            
        except Exception as e:
            self.logger.error(f"主机发现失败: {e}")
    
    def _get_manual_hosts(self) -> List[str]:
        """获取手动配置的主机"""
        try:
            # 从本地Agent获取手动配置的主机
            response = requests.get(
                f"http://127.0.0.1:{self.config.AGENT_PORT}/api/hosts",
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                hosts = response.json()
                self.logger.debug(f"获取到 {len(hosts)} 个手动配置的主机")
                return hosts
            else:
                self.logger.warning(f"获取手动配置主机失败: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取手动配置主机异常: {e}")
            return []
    
    def _check_hosts_health(self):
        """检查主机健康状态"""
        with self.cache_lock:
            hosts_to_check = list(self.hosts_cache.values())
        
        for host in hosts_to_check:
            try:
                # 检查主机是否在线
                is_online = self.network_utils.is_port_open(host.ip, self.config.AGENT_PORT)
                
                with self.cache_lock:
                    if is_online:
                        if host.status != HostStatus.ONLINE:
                            self.logger.info(f"主机上线: {host.ip}")
                        host.status = HostStatus.ONLINE
                        host.last_seen = datetime.now()
                        
                        # 更新主机信息
                        self._update_host_info(host)
                    else:
                        if host.status != HostStatus.OFFLINE:
                            self.logger.warning(f"主机离线: {host.ip}")
                        host.status = HostStatus.OFFLINE
                        
            except Exception as e:
                self.logger.error(f"检查主机 {host.ip} 健康状态异常: {e}")
                with self.cache_lock:
                    host.status = HostStatus.UNKNOWN
    
    def _update_host_info(self, host: Host):
        """更新主机信息"""
        try:
            # 获取串口信息
            serials_response = requests.get(
                f"http://{host.ip}:{self.config.AGENT_PORT}/api/serials",
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if serials_response.status_code == 200:
                serials_data = serials_response.json()
                host.serial_ports = [SerialPort(**port_data) for port_data in serials_data]
            
            # 获取测试用例信息
            cases_response = requests.get(
                f"http://{host.ip}:{self.config.AGENT_PORT}/api/cases",
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if cases_response.status_code == 200:
                cases_data = cases_response.json()
                host.test_cases = [TestCase(**case_data) for case_data in cases_data]
            
        except Exception as e:
            self.logger.error(f"更新主机 {host.ip} 信息失败: {e}")
    
    def get_hosts(self) -> List[Host]:
        """获取所有主机"""
        with self.cache_lock:
            return list(self.hosts_cache.values())
    
    def get_host(self, host_ip: str) -> Optional[Host]:
        """获取指定主机"""
        with self.cache_lock:
            return self.hosts_cache.get(host_ip)
    
    def get_host_serials(self, host_ip: str) -> List[SerialPort]:
        """获取主机串口列表"""
        host = self.get_host(host_ip)
        if host and host.status == HostStatus.ONLINE:
            return host.serial_ports
        return []
    
    def get_host_cases(self, host_ip: str) -> List[TestCase]:
        """获取主机测试用例列表"""
        host = self.get_host(host_ip)
        if host and host.status == HostStatus.ONLINE:
            return host.test_cases
        return []
    
    def run_test_on_host(self, host_ip: str, case_name: str, serial_port: str) -> ApiResponse:
        """在指定主机上运行测试"""
        try:
            host = self.get_host(host_ip)
            if not host:
                return ApiResponse(
                    success=False,
                    message=f"主机不存在: {host_ip}",
                    error_code="HOST_NOT_FOUND"
                )
            
            if host.status != HostStatus.ONLINE:
                return ApiResponse(
                    success=False,
                    message=f"主机离线: {host_ip}",
                    error_code="HOST_OFFLINE"
                )
            
            # 调用Agent API运行测试
            response = requests.post(
                f"http://{host_ip}:{self.config.AGENT_PORT}/api/test/run",
                json={
                    "case_name": case_name,
                    "serial_port": serial_port
                },
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                result_data = response.json()
                return ApiResponse(
                    success=True,
                    data=result_data.get('data'),
                    message=result_data.get('message', '测试已启动')
                )
            else:
                error_data = response.json()
                return ApiResponse(
                    success=False,
                    message=error_data.get('message', '启动测试失败'),
                    error_code=error_data.get('error_code', 'REMOTE_ERROR')
                )
                
        except Exception as e:
            self.logger.error(f"在主机 {host_ip} 上运行测试失败: {e}")
            return ApiResponse(
                success=False,
                message=f"运行测试失败: {str(e)}",
                error_code="REQUEST_ERROR"
            )
    
    def get_test_result_from_host(self, host_ip: str, test_id: str) -> Optional[Dict[str, Any]]:
        """从主机获取测试结果"""
        try:
            host = self.get_host(host_ip)
            if not host or host.status != HostStatus.ONLINE:
                return None
            
            response = requests.get(
                f"http://{host_ip}:{self.config.AGENT_PORT}/api/test/{test_id}",
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"从主机 {host_ip} 获取测试结果失败: {e}")
            return None
    
    def refresh_host(self, host_ip: str) -> ApiResponse:
        """刷新指定主机信息"""
        try:
            host = self.get_host(host_ip)
            if not host:
                return ApiResponse(
                    success=False,
                    message=f"主机不存在: {host_ip}",
                    error_code="HOST_NOT_FOUND"
                )
            
            # 检查主机状态
            is_online = self.network_utils.is_port_open(host_ip, self.config.AGENT_PORT)
            
            with self.cache_lock:
                if is_online:
                    host.status = HostStatus.ONLINE
                    host.last_seen = datetime.now()
                    self._update_host_info(host)
                else:
                    host.status = HostStatus.OFFLINE
            
            return ApiResponse(
                success=True,
                data=host.to_dict(),
                message="主机信息已刷新"
            )
            
        except Exception as e:
            self.logger.error(f"刷新主机 {host_ip} 信息失败: {e}")
            return ApiResponse(
                success=False,
                message=f"刷新主机信息失败: {str(e)}",
                error_code="REFRESH_ERROR"
            )
    
    def add_host(self, host_ip: str, host_name: str = None) -> ApiResponse:
        """添加主机"""
        try:
            # 检查主机是否已存在
            if self.get_host(host_ip):
                return ApiResponse(
                    success=False,
                    message=f"主机已存在: {host_ip}",
                    error_code="HOST_EXISTS"
                )
            
            # 验证IP格式
            import ipaddress
            try:
                ipaddress.ip_address(host_ip)
            except ValueError:
                return ApiResponse(
                    success=False,
                    message=f"无效的IP地址: {host_ip}",
                    error_code="INVALID_IP"
                )
            
            # 创建新主机
            new_host = Host(
                ip=host_ip,
                name=host_name or f"Host-{host_ip}",
                status=HostStatus.UNKNOWN,
                last_seen=datetime.now()
            )
            
            # 检查主机是否在线
            is_online = self.network_utils.is_port_open(host_ip, self.config.AGENT_PORT)
            
            with self.cache_lock:
                if is_online:
                    new_host.status = HostStatus.ONLINE
                    self._update_host_info(new_host)
                else:
                    new_host.status = HostStatus.OFFLINE
                
                self.hosts_cache[host_ip] = new_host
            
            # 保存到手动配置文件
            self._save_manual_host(host_ip, host_name)
            
            self.logger.info(f"已添加主机: {host_ip}")
            return ApiResponse(
                success=True,
                data=new_host.to_dict(),
                message="主机添加成功"
            )
            
        except Exception as e:
            self.logger.error(f"添加主机 {host_ip} 失败: {e}")
            return ApiResponse(
                success=False,
                message=f"添加主机失败: {str(e)}",
                error_code="ADD_HOST_ERROR"
            )
    
    def delete_host(self, host_ip: str) -> ApiResponse:
        """删除主机"""
        try:
            host = self.get_host(host_ip)
            if not host:
                return ApiResponse(
                    success=False,
                    message=f"主机不存在: {host_ip}",
                    error_code="HOST_NOT_FOUND"
                )
            
            # 从缓存中删除
            with self.cache_lock:
                del self.hosts_cache[host_ip]
            
            # 从手动配置文件中删除
            self._remove_manual_host(host_ip)
            
            self.logger.info(f"已删除主机: {host_ip}")
            return ApiResponse(
                success=True,
                message="主机删除成功"
            )
            
        except Exception as e:
            self.logger.error(f"删除主机 {host_ip} 失败: {e}")
            return ApiResponse(
                success=False,
                message=f"删除主机失败: {str(e)}",
                error_code="DELETE_HOST_ERROR"
            )
    
    def update_host(self, host_ip: str, host_name: str = None) -> ApiResponse:
        """更新主机信息"""
        try:
            host = self.get_host(host_ip)
            if not host:
                return ApiResponse(
                    success=False,
                    message=f"主机不存在: {host_ip}",
                    error_code="HOST_NOT_FOUND"
                )
            
            # 更新主机名称
            if host_name:
                with self.cache_lock:
                    host.name = host_name
                
                # 更新手动配置文件
                self._save_manual_host(host_ip, host_name)
            
            # 刷新主机信息
            is_online = self.network_utils.is_port_open(host_ip, self.config.AGENT_PORT)
            
            with self.cache_lock:
                if is_online:
                    host.status = HostStatus.ONLINE
                    host.last_seen = datetime.now()
                    self._update_host_info(host)
                else:
                    host.status = HostStatus.OFFLINE
            
            self.logger.info(f"已更新主机: {host_ip}")
            return ApiResponse(
                success=True,
                data=host.to_dict(),
                message="主机更新成功"
            )
            
        except Exception as e:
            self.logger.error(f"更新主机 {host_ip} 失败: {e}")
            return ApiResponse(
                success=False,
                message=f"更新主机失败: {str(e)}",
                error_code="UPDATE_HOST_ERROR"
            )
    
    def _save_manual_host(self, host_ip: str, host_name: str = None):
        """保存手动配置的主机到文件"""
        try:
            manual_hosts_file = self.config.MANUAL_HOSTS_FILE
            
            # 读取现有配置
            manual_hosts = []
            if os.path.exists(manual_hosts_file):
                with open(manual_hosts_file, 'r', encoding='utf-8') as f:
                    manual_hosts = json.load(f)
            
            # 更新或添加主机
            host_found = False
            for host in manual_hosts:
                if host['ip'] == host_ip:
                    if host_name:
                        host['name'] = host_name
                    host_found = True
                    break
            
            if not host_found:
                manual_hosts.append({
                    'ip': host_ip,
                    'name': host_name or f"Host-{host_ip}"
                })
            
            # 保存配置
            os.makedirs(os.path.dirname(manual_hosts_file), exist_ok=True)
            with open(manual_hosts_file, 'w', encoding='utf-8') as f:
                json.dump(manual_hosts, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存手动配置主机失败: {e}")
    
    def _remove_manual_host(self, host_ip: str):
        """从手动配置文件中删除主机"""
        try:
            manual_hosts_file = self.config.MANUAL_HOSTS_FILE
            
            if not os.path.exists(manual_hosts_file):
                return
            
            # 读取现有配置
            with open(manual_hosts_file, 'r', encoding='utf-8') as f:
                manual_hosts = json.load(f)
            
            # 删除指定主机
            manual_hosts = [host for host in manual_hosts if host['ip'] != host_ip]
            
            # 保存配置
            with open(manual_hosts_file, 'w', encoding='utf-8') as f:
                json.dump(manual_hosts, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"删除手动配置主机失败: {e}")