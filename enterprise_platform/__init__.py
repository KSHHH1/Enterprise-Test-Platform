"""
企业测试平台 - 主模块
版本: 2.0.0
作者: AI Assistant
描述: 企业级串口测试平台，支持分布式测试机管理
"""

__version__ = "2.0.0"
__author__ = "AI Assistant"
__description__ = "企业级串口测试平台"

from .config import get_config, Config
from .core import AgentCore, AgentAPI, CenterCore, CenterAPI
from .utils import get_logger, NetworkUtils, SerialUtils, FileUtils
from .models import Host, SerialPort, TestCase, TestResult, ApiResponse

__all__ = [
    # 配置
    'get_config', 'Config',
    
    # 核心模块
    'AgentCore', 'AgentAPI', 'CenterCore', 'CenterAPI',
    
    # 工具模块
    'get_logger', 'NetworkUtils', 'SerialUtils', 'FileUtils',
    
    # 数据模型
    'Host', 'SerialPort', 'TestCase', 'TestResult', 'ApiResponse'
]