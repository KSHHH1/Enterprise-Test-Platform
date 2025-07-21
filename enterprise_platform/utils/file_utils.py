"""
企业测试平台 - 文件工具模块
"""
import os
import json
from typing import List, Dict, Any, Optional
from ..config import get_config
from .logger import get_logger

logger = get_logger('enterprise_platform.file')

class FileUtils:
    """文件工具类"""
    
    def __init__(self, config_name: str = None):
        self.config = get_config(config_name)
    
    def find_test_cases_directory(self) -> Optional[str]:
        """查找测试用例目录"""
        for dir_path in self.config.TEST_CASES_DIRS:
            # 支持相对路径和绝对路径
            if not os.path.isabs(dir_path):
                # 相对于当前文件的路径
                current_dir = os.path.dirname(os.path.abspath(__file__))
                dir_path = os.path.abspath(os.path.join(current_dir, '..', '..', dir_path))
            
            logger.debug(f"检查测试用例目录: {dir_path}")
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                logger.info(f"找到测试用例目录: {dir_path}")
                return dir_path
        
        logger.warning("未找到测试用例目录")
        return None
    
    def list_test_cases(self) -> List[Dict[str, Any]]:
        """获取测试用例列表"""
        case_dir = self.find_test_cases_directory()
        
        if not case_dir:
            logger.info("未找到测试用例目录，返回示例用例")
            return self._get_sample_cases()
        
        cases = []
        try:
            for file in os.listdir(case_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    case_info = {
                        "name": file,
                        "display_name": file.replace('_', ' ').replace('.py', '').title(),
                        "path": os.path.join(case_dir, file),
                        "is_sample": False,
                        "size": os.path.getsize(os.path.join(case_dir, file))
                    }
                    cases.append(case_info)
                    logger.debug(f"发现测试用例: {case_info['name']}")
            
            logger.info(f"找到 {len(cases)} 个测试用例")
            return cases
            
        except Exception as e:
            logger.error(f"列举测试用例异常: {e}")
            return self._get_sample_cases()
    
    def find_test_case_path(self, case_name: str) -> Optional[str]:
        """查找测试用例的完整路径"""
        case_dir = self.find_test_cases_directory()
        
        if not case_dir:
            logger.warning(f"未找到测试用例目录，无法定位: {case_name}")
            return None
        
        case_path = os.path.join(case_dir, case_name)
        if os.path.exists(case_path):
            logger.debug(f"找到测试用例: {case_path}")
            return case_path
        
        logger.warning(f"测试用例不存在: {case_path}")
        return None
    
    @staticmethod
    def _get_sample_cases() -> List[Dict[str, Any]]:
        """获取示例测试用例"""
        return [
            {
                "name": "basic_test.py",
                "display_name": "Basic Test",
                "path": "示例测试用例 - 基础串口测试",
                "is_sample": True,
                "size": 0
            },
            {
                "name": "loopback_test.py", 
                "display_name": "Loopback Test",
                "path": "示例测试用例 - 环回测试",
                "is_sample": True,
                "size": 0
            },
            {
                "name": "enhanced_basic_test.py",
                "display_name": "Enhanced Basic Test",
                "path": "示例测试用例 - 增强基础测试",
                "is_sample": True,
                "size": 0
            }
        ]

class JsonFileManager:
    """JSON文件管理器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.logger = get_logger(f'enterprise_platform.json_manager.{os.path.basename(file_path)}')
    
    def load(self, default_value: Any = None) -> Any:
        """加载JSON文件"""
        if not os.path.exists(self.file_path):
            self.logger.info(f"文件不存在，返回默认值: {self.file_path}")
            return default_value if default_value is not None else []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.debug(f"成功加载文件: {self.file_path}")
                return data
        except Exception as e:
            self.logger.error(f"加载文件失败 {self.file_path}: {e}")
            return default_value if default_value is not None else []
    
    def save(self, data: Any) -> bool:
        """保存数据到JSON文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"成功保存文件: {self.file_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存文件失败 {self.file_path}: {e}")
            return False