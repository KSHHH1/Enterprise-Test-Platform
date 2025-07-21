"""
企业测试平台 - 数据模型
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class HostStatus(Enum):
    """主机状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

class TestStatus(Enum):
    """测试状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class SerialPort:
    """串口信息"""
    device: str
    description: str = "未知设备"
    hwid: str = "未知硬件ID"
    is_virtual: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device": self.device,
            "description": self.description,
            "hwid": self.hwid,
            "is_virtual": self.is_virtual
        }

@dataclass
class TestCase:
    """测试用例信息"""
    name: str
    display_name: str = ""
    path: str = ""
    is_sample: bool = False
    size: int = 0
    
    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.name.replace('_', ' ').replace('.py', '').title()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "path": self.path,
            "is_sample": self.is_sample,
            "size": self.size
        }

@dataclass
class Host:
    """主机信息"""
    ip: str
    name: str = ""
    status: HostStatus = HostStatus.UNKNOWN
    serial_ports: List[SerialPort] = field(default_factory=list)
    test_cases: List[TestCase] = field(default_factory=list)
    last_seen: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.name:
            self.name = f"主机-{self.ip}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ip": self.ip,
            "name": self.name,
            "status": self.status.value,
            "serial_ports": [port.to_dict() for port in self.serial_ports],
            "test_cases": [case.to_dict() for case in self.test_cases],
            "last_seen": self.last_seen.isoformat() if self.last_seen else None
        }

@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    host_ip: str
    case_name: str
    serial_port: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    output: str = ""
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "host_ip": self.host_ip,
            "case_name": self.case_name,
            "serial_port": self.serial_port,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "output": self.output,
            "error": self.error
        }

@dataclass
class ApiResponse:
    """API响应模型"""
    success: bool
    data: Any = None
    message: str = ""
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "data": self.data,
            "message": self.message
        }
        if self.error_code:
            result["error_code"] = self.error_code
        return result