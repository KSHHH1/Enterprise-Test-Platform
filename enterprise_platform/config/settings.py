"""
企业测试平台 - 配置管理模块
"""
import os
from typing import Dict, Any

class Config:
    """基础配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 端口配置
    AGENT_PORT = int(os.environ.get('AGENT_PORT', 5001))
    CENTER_PORT = int(os.environ.get('CENTER_PORT', 5002))
    
    # 测试用例配置
    TEST_CASES_DIRS = [
        os.path.join(os.getcwd(), 'test_cases'),
        os.path.join(os.getcwd(), 'cases'),
        os.path.join(os.getcwd(), 'tests')
    ]
    
    # 手动配置主机文件
    MANUAL_HOSTS_FILE = os.path.join(os.getcwd(), 'manual_hosts.json')
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DIR = os.path.join(os.getcwd(), 'logs')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 网络配置
    HOST_DISCOVERY_INTERVAL = 30  # 主机发现间隔（秒）
    HEALTH_CHECK_INTERVAL = 10    # 健康检查间隔（秒）
    NETWORK_TIMEOUT = 5           # 网络超时（秒）
    REQUEST_TIMEOUT = 5           # 请求超时（秒）
    SOCKET_TIMEOUT = 2            # Socket超时（秒）
    AGENT_TIMEOUT = 3             # Agent超时（秒）
    DISCOVERY_TIMEOUT = 10        # 发现超时（秒）
    
    # 测试配置
    TEST_TIMEOUT = 300            # 测试超时（秒）
    MAX_CONCURRENT_TESTS = 5      # 最大并发测试数
    
    # 数据库配置（预留）
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///enterprise_platform.db')
    
    # 网络扫描配置
    MAX_SCAN_WORKERS = int(os.environ.get('MAX_SCAN_WORKERS', 100))
    COMMON_IP_RANGES = [
        list(range(1, 10)),      # 1-9 (路由器等)
        list(range(20, 40)),     # 20-39 (常用设备)
        list(range(100, 120)),   # 100-119 (DHCP常用范围)
        list(range(200, 210))    # 200-209 (静态IP常用)
    ]
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建必要的目录
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        for test_dir in Config.TEST_CASES_DIRS:
            os.makedirs(test_dir, exist_ok=True)

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # 开发环境特定配置
    AGENT_TIMEOUT = 1
    DISCOVERY_TIMEOUT = 3

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # 生产环境特定配置
    AGENT_TIMEOUT = 5
    DISCOVERY_TIMEOUT = 10

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # 测试环境特定配置
    DATABASE_URL = 'sqlite:///:memory:'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: str = None) -> Config:
    """获取配置对象"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    config_class = config.get(config_name, config['default'])
    return config_class()