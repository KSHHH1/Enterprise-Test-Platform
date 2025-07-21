"""
企业测试平台 - 网络工具模块
"""
import socket
import concurrent.futures
from typing import List, Dict, Any, Optional
import requests
from ..config import get_config
from .logger import network_logger

class NetworkUtils:
    """网络工具类"""
    
    def __init__(self, config_name: str = None):
        self.config = get_config(config_name)
        self.logger = network_logger
    
    def is_port_open(self, ip: str, port: int, timeout: float = None) -> bool:
        """检查端口是否开放"""
        if timeout is None:
            timeout = self.config.SOCKET_TIMEOUT
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                result = s.connect_ex((ip, port))
                return result == 0
        except Exception as e:
            self.logger.debug(f"检查端口 {ip}:{port} 失败: {e}")
            return False
    
    def get_agent_info(self, ip: str, port: int = None, timeout: int = None) -> Optional[Dict[str, Any]]:
        """获取Agent信息"""
        if port is None:
            port = self.config.AGENT_PORT
        if timeout is None:
            timeout = self.config.AGENT_TIMEOUT
        
        try:
            url = f'http://{ip}:{port}/info'
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                info = response.json()
                self.logger.debug(f"成功获取 {ip} 的Agent信息: {info}")
                return info
            else:
                self.logger.warning(f"获取 {ip} Agent信息失败: HTTP {response.status_code}")
                return None
        except Exception as e:
            self.logger.debug(f"获取 {ip} Agent信息异常: {e}")
            return None
    
    def get_local_network_segments(self) -> List[str]:
        """获取本机所在的网络段"""
        segments = []
        
        try:
            import netifaces
            import ipaddress
            
            interfaces = netifaces.interfaces()
            self.logger.debug(f"发现网络接口: {interfaces}")
            
            for interface in interfaces:
                try:
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        for addr_info in addrs[netifaces.AF_INET]:
                            ip = addr_info.get('addr')
                            netmask = addr_info.get('netmask')
                            if ip and netmask and not ip.startswith('127.'):
                                try:
                                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                                    network_base = str(network.network_address)
                                    segment = '.'.join(network_base.split('.')[:-1])
                                    if segment not in segments:
                                        segments.append(segment)
                                        self.logger.debug(f"添加网络段: {segment} (接口: {interface}, IP: {ip})")
                                except Exception as e:
                                    self.logger.debug(f"解析网络 {ip}/{netmask} 失败: {e}")
                                    continue
                except Exception as e:
                    self.logger.debug(f"处理接口 {interface} 失败: {e}")
                    continue
                    
        except ImportError:
            self.logger.warning("netifaces库不可用，使用默认网段")
            segments = ['192.168.1', '192.168.0', '192.168.20', '10.0.0', '172.16.0']
        except Exception as e:
            self.logger.error(f"获取网络接口失败: {e}")
            segments = ['192.168.1', '192.168.0', '192.168.20', '10.0.0', '172.16.0']
        
        # 强制添加常用网段
        default_segments = ['192.168.20', '192.168.1', '192.168.0']
        for seg in default_segments:
            if seg not in segments:
                segments.append(seg)
        
        if not segments:
            segments = default_segments
        
        self.logger.info(f"最终扫描网段: {segments}")
        return segments
    
    def discover_agents(self, max_workers: int = None, timeout: int = None) -> List[Dict[str, Any]]:
        """发现网络中的Agent"""
        if max_workers is None:
            max_workers = self.config.MAX_SCAN_WORKERS
        if timeout is None:
            timeout = self.config.DISCOVERY_TIMEOUT
        
        discovered = []
        network_segments = self.get_local_network_segments()
        
        self.logger.info(f"开始快速Agent发现，网段: {network_segments}")
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                
                # 扫描常用IP范围
                for segment in network_segments:
                    for ip_range in self.config.COMMON_IP_RANGES:
                        for i in ip_range:
                            ip = f'{segment}.{i}'
                            future = executor.submit(self.is_port_open, ip, self.config.AGENT_PORT)
                            futures[future] = ip
                
                self.logger.debug(f"提交了 {len(futures)} 个扫描任务")
                
                for future in concurrent.futures.as_completed(futures, timeout=timeout):
                    try:
                        if future.result():
                            ip = futures[future]
                            self.logger.info(f"发现在线Agent: {ip}")
                            
                            info = self.get_agent_info(ip)
                            if info:
                                discovered.append({
                                    "name": info.get('hostname', f'测试机-{ip.split(".")[-1]}'),
                                    "ip": ip,
                                    "location": info.get('location', '自动发现'),
                                    "status": "空闲",
                                    "type": "auto",
                                    "agent_info": info
                                })
                            else:
                                discovered.append({
                                    "name": f'测试机-{ip.split(".")[-1]}',
                                    "ip": ip,
                                    "location": '自动发现',
                                    "status": "空闲",
                                    "type": "auto"
                                })
                    except Exception as e:
                        self.logger.debug(f"处理扫描结果异常: {e}")
                        continue
                        
        except concurrent.futures.TimeoutError:
            self.logger.warning("Agent发现超时，返回部分结果")
        except Exception as e:
            self.logger.error(f"Agent发现过程异常: {e}")
        
        self.logger.info(f"Agent发现完成，找到 {len(discovered)} 个主机")
        return discovered