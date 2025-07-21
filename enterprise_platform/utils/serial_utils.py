"""
企业测试平台 - 串口工具模块
"""
from typing import List, Dict, Any, Optional
from .logger import get_logger

logger = get_logger('enterprise_platform.serial')

class SerialUtils:
    """串口工具类"""
    
    @staticmethod
    def safe_import_serial():
        """安全导入serial库"""
        try:
            import serial.tools.list_ports
            return serial.tools.list_ports
        except ImportError:
            logger.warning("pyserial库未安装")
            return None
    
    @classmethod
    def list_serial_ports(cls) -> List[Dict[str, Any]]:
        """获取可用串口列表"""
        try:
            serial_tools = cls.safe_import_serial()
            if not serial_tools:
                return cls._get_virtual_ports("pyserial库未安装，无法检测串口")
            
            ports = []
            try:
                for p in serial_tools.comports():
                    port_info = {
                        "device": p.device,
                        "description": getattr(p, 'description', '未知设备'),
                        "hwid": getattr(p, 'hwid', '未知硬件ID'),
                        "is_virtual": False
                    }
                    ports.append(port_info)
                    logger.debug(f"发现串口: {port_info}")
            except Exception as e:
                logger.error(f"枚举串口时出错: {e}")
            
            # 如果没有找到串口，返回虚拟串口
            if not ports:
                return cls._get_virtual_ports("未检测到真实串口，显示虚拟串口用于测试")
            
            logger.info(f"发现 {len(ports)} 个串口")
            return ports
            
        except Exception as e:
            logger.error(f"获取串口列表异常: {e}")
            return cls._get_virtual_ports(f"获取串口时出错: {str(e)}，显示虚拟串口")
    
    @staticmethod
    def _get_virtual_ports(message: str = None) -> List[Dict[str, Any]]:
        """获取虚拟串口列表"""
        virtual_ports = [
            {
                "device": "COM1", 
                "description": "虚拟串口1 (测试用)", 
                "hwid": "VIRTUAL_001",
                "is_virtual": True
            },
            {
                "device": "COM2", 
                "description": "虚拟串口2 (测试用)", 
                "hwid": "VIRTUAL_002",
                "is_virtual": True
            },
            {
                "device": "COM3", 
                "description": "虚拟串口3 (测试用)", 
                "hwid": "VIRTUAL_003",
                "is_virtual": True
            }
        ]
        
        if message:
            logger.info(message)
        
        return virtual_ports
    
    @staticmethod
    def validate_port(port_name: str) -> bool:
        """验证串口名称是否有效"""
        if not port_name:
            return False
        
        # Windows COM端口格式验证
        if port_name.upper().startswith('COM'):
            try:
                port_num = int(port_name[3:])
                return 1 <= port_num <= 256
            except ValueError:
                return False
        
        # Linux/Unix 串口格式验证
        if port_name.startswith('/dev/'):
            return True
        
        return False