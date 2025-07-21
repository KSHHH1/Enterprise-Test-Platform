"""
企业测试平台 - 日志工具模块
"""
import logging
import logging.handlers
import os
from typing import Optional
from ..config import get_config

class Logger:
    """统一日志管理器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, config_name: str = None) -> logging.Logger:
        """获取日志记录器"""
        if name in cls._loggers:
            return cls._loggers[name]
        
        config = get_config(config_name)
        logger = logging.getLogger(name)
        
        # 避免重复添加处理器
        if not logger.handlers:
            logger.setLevel(getattr(logging, config.LOG_LEVEL))
            
            # 创建格式化器
            formatter = logging.Formatter(config.LOG_FORMAT)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # 文件处理器（带轮转）
            if hasattr(config, 'LOG_DIR') and config.LOG_DIR:
                # 确保日志目录存在
                if not os.path.exists(config.LOG_DIR):
                    os.makedirs(config.LOG_DIR)
                
                log_file = os.path.join(config.LOG_DIR, f'{name}.log')
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=getattr(config, 'LOG_MAX_BYTES', 10*1024*1024),  # 10MB
                    backupCount=getattr(config, 'LOG_BACKUP_COUNT', 5),
                    encoding='utf-8'
                )
                file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger

def get_logger(name: str, config_name: str = None) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return Logger.get_logger(name, config_name)

# 预定义的日志记录器
agent_logger = get_logger('enterprise_platform.agent')
center_logger = get_logger('enterprise_platform.center')
network_logger = get_logger('enterprise_platform.network')
test_logger = get_logger('enterprise_platform.test')