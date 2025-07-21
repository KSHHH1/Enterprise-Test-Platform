"""
测试机状态管理和互斥锁机制
防止多用户同时操作同一台测试机
"""
import time
import threading
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

class TestMachineStatus(Enum):
    """测试机状态枚举"""
    IDLE = "idle"           # 空闲
    BUSY = "busy"           # 忙碌中
    LOCKED = "locked"       # 被锁定
    OFFLINE = "offline"     # 离线
    MAINTENANCE = "maintenance"  # 维护中

@dataclass
class TestSession:
    """测试会话信息"""
    session_id: str
    user_id: str
    user_name: str
    machine_ip: str
    test_case: str
    serial_port: str
    start_time: datetime
    last_heartbeat: datetime
    status: str
    test_id: Optional[str] = None
    
    def to_dict(self):
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'machine_ip': self.machine_ip,
            'test_case': self.test_case,
            'serial_port': self.serial_port,
            'start_time': self.start_time.isoformat(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'status': self.status,
            'test_id': self.test_id
        }

class TestMachineManager:
    """测试机状态管理器"""
    
    def __init__(self, session_timeout: int = 300):  # 5分钟超时
        self.session_timeout = session_timeout
        self.sessions: Dict[str, TestSession] = {}  # machine_ip -> TestSession
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of machine_ips
        self.lock = threading.RLock()
        self.status_file = "machine_status.json"
        self.load_status()
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        self.cleanup_thread.start()
    
    def load_status(self):
        """从文件加载状态"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for machine_ip, session_data in data.get('sessions', {}).items():
                        session = TestSession(
                            session_id=session_data['session_id'],
                            user_id=session_data['user_id'],
                            user_name=session_data['user_name'],
                            machine_ip=session_data['machine_ip'],
                            test_case=session_data['test_case'],
                            serial_port=session_data['serial_port'],
                            start_time=datetime.fromisoformat(session_data['start_time']),
                            last_heartbeat=datetime.fromisoformat(session_data['last_heartbeat']),
                            status=session_data['status'],
                            test_id=session_data.get('test_id')
                        )
                        self.sessions[machine_ip] = session
                        
                        # 重建用户会话索引
                        if session.user_id not in self.user_sessions:
                            self.user_sessions[session.user_id] = set()
                        self.user_sessions[session.user_id].add(machine_ip)
        except Exception as e:
            print(f"加载状态文件失败: {e}")
    
    def save_status(self):
        """保存状态到文件"""
        try:
            data = {
                'sessions': {ip: session.to_dict() for ip, session in self.sessions.items()},
                'last_update': datetime.now().isoformat()
            }
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存状态文件失败: {e}")
    
    def acquire_machine(self, machine_ip: str, user_id: str, user_name: str, 
                       test_case: str = "手动占用", serial_port: str = "", manual: bool = False) -> tuple[bool, str]:
        """
        获取测试机使用权
        参数:
            machine_ip: 测试机IP
            user_id: 用户ID
            user_name: 用户名
            test_case: 测试用例名称
            serial_port: 串口
            manual: 是否为手动占用
        返回: (是否成功, 消息)
        """
        with self.lock:
            # 检查机器是否已被占用
            if machine_ip in self.sessions:
                current_session = self.sessions[machine_ip]
                if self._is_session_valid(current_session):
                    # 如果是同一个用户，允许继续使用
                    if current_session.user_id == user_id:
                        # 更新心跳和测试用例信息
                        current_session.last_heartbeat = datetime.now()
                        if test_case and test_case != "手动占用":
                            current_session.test_case = test_case
                        if serial_port:
                            current_session.serial_port = serial_port
                        self.save_status()
                        return True, f"继续使用测试机 {machine_ip}"
                    else:
                        return False, f"测试机正在被用户 {current_session.user_name} 使用"
                else:
                    # 会话已过期，清理
                    self._cleanup_session(machine_ip)
            
            # 如果不是手动占用，检查用户是否已经在使用其他机器
            if not manual and user_id in self.user_sessions and self.user_sessions[user_id]:
                active_machines = []
                for ip in list(self.user_sessions[user_id]):
                    if ip in self.sessions and self._is_session_valid(self.sessions[ip]):
                        active_machines.append(ip)
                    else:
                        self.user_sessions[user_id].discard(ip)
                
                if active_machines:
                    return False, f"您正在使用其他测试机: {', '.join(active_machines)}"
            
            # 创建新会话
            session_id = f"session_{int(time.time())}_{user_id}_{machine_ip}"
            session = TestSession(
                session_id=session_id,
                user_id=user_id,
                user_name=user_name,
                machine_ip=machine_ip,
                test_case=test_case if test_case else ("手动占用" if manual else "未知测试"),
                serial_port=serial_port,
                start_time=datetime.now(),
                last_heartbeat=datetime.now(),
                status="manual" if manual else "active"
            )
            
            self.sessions[machine_ip] = session
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(machine_ip)
            
            self.save_status()
            action_type = "手动占用" if manual else "获取"
            return True, f"成功{action_type}测试机 {machine_ip} 使用权"
    
    def release_machine(self, machine_ip: str, user_id: str) -> tuple[bool, str]:
        """
        释放测试机使用权
        返回: (是否成功, 消息)
        """
        with self.lock:
            if machine_ip not in self.sessions:
                return False, "测试机未被占用"
            
            session = self.sessions[machine_ip]
            if session.user_id != user_id:
                return False, f"无权释放，测试机正在被用户 {session.user_name} 使用"
            
            self._cleanup_session(machine_ip)
            self.save_status()
            return True, f"成功释放测试机 {machine_ip}"
    
    def update_heartbeat(self, machine_ip: str, user_id: str, test_id: str = None) -> tuple[bool, str]:
        """
        更新心跳，保持会话活跃
        返回: (是否成功, 消息)
        """
        with self.lock:
            if machine_ip not in self.sessions:
                return False, "会话不存在"
            
            session = self.sessions[machine_ip]
            if session.user_id != user_id:
                return False, "用户不匹配"
            
            session.last_heartbeat = datetime.now()
            if test_id:
                session.test_id = test_id
            
            self.save_status()
            return True, "心跳更新成功"
    
    def get_machine_status(self, machine_ip: str) -> Dict:
        """获取测试机状态"""
        with self.lock:
            if machine_ip not in self.sessions:
                return {
                    'status': TestMachineStatus.IDLE.value,
                    'available': True,
                    'message': '空闲'
                }
            
            session = self.sessions[machine_ip]
            if not self._is_session_valid(session):
                self._cleanup_session(machine_ip)
                return {
                    'status': TestMachineStatus.IDLE.value,
                    'available': True,
                    'message': '空闲'
                }
            
            return {
                'status': TestMachineStatus.BUSY.value,
                'available': False,
                'message': f'正在被 {session.user_name} 使用',
                'session': session.to_dict()
            }
    
    def get_all_machine_status(self) -> Dict[str, Dict]:
        """获取所有测试机状态"""
        with self.lock:
            result = {}
            
            # 首先获取网络中发现的所有在线Agent
            try:
                from ...utils import NetworkUtils
                network_utils = NetworkUtils()
                discovered_agents = network_utils.discover_agents()
                
                # 为每个发现的Agent添加状态信息
                for agent in discovered_agents:
                    machine_ip = agent.get('ip')
                    if machine_ip:
                        # 获取该机器的状态（占用或空闲）
                        machine_status = self.get_machine_status(machine_ip)
                        
                        # 添加Agent的详细信息
                        result[machine_ip] = {
                            **machine_status,
                            'agent_info': agent,
                            'occupied': machine_ip in self.sessions and self._is_session_valid(self.sessions[machine_ip])
                        }
                        
                        # 如果机器被占用，添加占用者信息
                        if machine_ip in self.sessions and self._is_session_valid(self.sessions[machine_ip]):
                            session = self.sessions[machine_ip]
                            result[machine_ip]['occupied_by'] = session.user_name
                            result[machine_ip]['occupied_by_id'] = session.user_id
                            result[machine_ip]['test_case'] = session.test_case
                            result[machine_ip]['start_time'] = session.start_time.isoformat()
                            result[machine_ip]['last_heartbeat'] = session.last_heartbeat.isoformat()
                        
            except Exception as e:
                print(f"网络发现失败，回退到仅显示已占用机器: {e}")
                # 如果网络发现失败，回退到原来的逻辑
                for machine_ip in self.sessions:
                    result[machine_ip] = self.get_machine_status(machine_ip)
            
            return result
    
    def get_user_sessions(self, user_id: str) -> list[Dict]:
        """获取用户的所有活跃会话"""
        with self.lock:
            sessions = []
            if user_id in self.user_sessions:
                for machine_ip in self.user_sessions[user_id]:
                    if machine_ip in self.sessions:
                        session = self.sessions[machine_ip]
                        if self._is_session_valid(session):
                            sessions.append(session.to_dict())
            return sessions
    
    def force_release_machine(self, machine_ip: str, admin_user: str) -> tuple[bool, str]:
        """
        管理员强制释放测试机
        返回: (是否成功, 消息)
        """
        with self.lock:
            if machine_ip not in self.sessions:
                return False, "测试机未被占用"
            
            session = self.sessions[machine_ip]
            old_user = session.user_name
            self._cleanup_session(machine_ip)
            self.save_status()
            
            return True, f"管理员 {admin_user} 强制释放了被 {old_user} 占用的测试机 {machine_ip}"
    
    def _is_session_valid(self, session: TestSession) -> bool:
        """检查会话是否有效（未超时）"""
        now = datetime.now()
        return (now - session.last_heartbeat).total_seconds() < self.session_timeout
    
    def _cleanup_session(self, machine_ip: str):
        """清理会话"""
        if machine_ip in self.sessions:
            session = self.sessions[machine_ip]
            user_id = session.user_id
            
            del self.sessions[machine_ip]
            
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(machine_ip)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
    
    def _cleanup_expired_sessions(self):
        """定期清理过期会话"""
        while True:
            try:
                time.sleep(60)  # 每分钟检查一次
                with self.lock:
                    expired_machines = []
                    for machine_ip, session in self.sessions.items():
                        if not self._is_session_valid(session):
                            expired_machines.append(machine_ip)
                    
                    for machine_ip in expired_machines:
                        print(f"清理过期会话: {machine_ip}")
                        self._cleanup_session(machine_ip)
                    
                    if expired_machines:
                        self.save_status()
            except Exception as e:
                print(f"清理过期会话时出错: {e}")

# 全局实例
machine_manager = TestMachineManager()

def get_machine_manager() -> TestMachineManager:
    """获取测试机管理器实例"""
    return machine_manager