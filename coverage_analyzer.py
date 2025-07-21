#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试覆盖率分析工具
由 TRAE AI 自动生成，用于分析代码测试覆盖情况
"""

import ast
import os
import sys
import json
from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    file_path: str
    line_number: int
    is_tested: bool = False
    test_cases: List[str] = None
    
    def __post_init__(self):
        if self.test_cases is None:
            self.test_cases = []


@dataclass
class CoverageReport:
    """覆盖率报告"""
    total_functions: int
    tested_functions: int
    coverage_percentage: float
    untested_functions: List[FunctionInfo]
    function_details: Dict[str, FunctionInfo]


class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.functions: Dict[str, FunctionInfo] = {}
        self.test_functions: Set[str] = set()
        
    def analyze_python_file(self, file_path: str) -> List[FunctionInfo]:
        """分析Python文件中的函数"""
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 跳过私有函数和测试函数
                    if not node.name.startswith('_') and not node.name.startswith('test_'):
                        func_info = FunctionInfo(
                            name=node.name,
                            file_path=file_path,
                            line_number=node.lineno
                        )
                        functions.append(func_info)
                        self.functions[node.name] = func_info
                        
        except Exception as e:
            print(f"分析文件失败 {file_path}: {e}")
            
        return functions
    
    def analyze_test_file(self, file_path: str) -> Set[str]:
        """分析测试文件，识别被测试的函数"""
        tested_functions = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 简单的字符串匹配来识别被测试的函数
            for func_name in self.functions.keys():
                if func_name in content:
                    tested_functions.add(func_name)
                    self.functions[func_name].is_tested = True
                    
                    # 查找测试用例名称
                    lines = content.split('\n')
                    for line in lines:
                        if f'def test_' in line and func_name in line:
                            test_case_name = line.strip().split('def ')[1].split('(')[0]
                            self.functions[func_name].test_cases.append(test_case_name)
                            
        except Exception as e:
            print(f"分析测试文件失败 {file_path}: {e}")
            
        return tested_functions
    
    def scan_project(self) -> CoverageReport:
        """扫描整个项目"""
        print("🔍 开始扫描项目...")
        
        # 扫描源代码文件
        for root, dirs, files in os.walk(self.project_root):
            # 跳过测试目录、缓存目录等
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'tests', 'test']]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = os.path.join(root, file)
                    self.analyze_python_file(file_path)
        
        print(f"📊 发现 {len(self.functions)} 个函数")
        
        # 扫描测试文件
        test_dir = os.path.join(self.project_root, 'tests')
        if os.path.exists(test_dir):
            for file in os.listdir(test_dir):
                if file.endswith('.py') and file.startswith('test_'):
                    file_path = os.path.join(test_dir, file)
                    self.analyze_test_file(file_path)
        
        # 生成报告
        tested_count = sum(1 for f in self.functions.values() if f.is_tested)
        total_count = len(self.functions)
        coverage_percentage = (tested_count / total_count * 100) if total_count > 0 else 0
        
        untested_functions = [f for f in self.functions.values() if not f.is_tested]
        
        return CoverageReport(
            total_functions=total_count,
            tested_functions=tested_count,
            coverage_percentage=coverage_percentage,
            untested_functions=untested_functions,
            function_details=self.functions
        )


class TestCaseGenerator:
    """测试用例生成器"""
    
    def __init__(self, coverage_report: CoverageReport):
        self.coverage_report = coverage_report
        
    def generate_test_template(self, function_info: FunctionInfo) -> str:
        """为函数生成测试模板"""
        template = f'''
    def test_{function_info.name}_success(self):
        """测试 {function_info.name} - 成功场景"""
        # TODO: 实现成功场景测试
        # 1. 准备测试数据
        # 2. 调用被测试函数
        # 3. 验证结果
        pass
        
    def test_{function_info.name}_failure(self):
        """测试 {function_info.name} - 失败场景"""
        # TODO: 实现失败场景测试
        # 1. 准备异常数据
        # 2. 调用被测试函数
        # 3. 验证异常处理
        pass
        
    def test_{function_info.name}_edge_cases(self):
        """测试 {function_info.name} - 边界情况"""
        # TODO: 实现边界情况测试
        # 1. 测试空值、None、边界值
        # 2. 验证边界处理逻辑
        pass
'''
        return template
    
    def generate_missing_tests(self) -> str:
        """生成缺失的测试用例"""
        if not self.coverage_report.untested_functions:
            return "# 所有函数都已有测试覆盖！"
            
        test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成的缺失测试用例
由 TRAE AI 测试覆盖率分析工具生成
"""

import unittest
from unittest.mock import patch, Mock, MagicMock

# TODO: 导入被测试的模块
# from your_module import function_name


class TestMissingCoverage(unittest.TestCase):
    """缺失覆盖率的测试用例"""
    
    def setUp(self):
        """测试前准备"""
        pass
'''
        
        for func_info in self.coverage_report.untested_functions:
            test_code += self.generate_test_template(func_info)
            
        test_code += '''

if __name__ == '__main__':
    unittest.main()
'''
        
        return test_code


def generate_mock_data_examples():
    """生成Mock数据示例"""
    examples = {
        "网络请求Mock": {
            "description": "模拟HTTP请求响应",
            "code": '''
# Mock HTTP 请求
@patch('requests.get')
def test_api_call(self, mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_get.return_value = mock_response
    
    # 执行测试
    result = your_function()
    self.assertEqual(result["status"], "success")
'''
        },
        
        "数据库Mock": {
            "description": "模拟数据库操作",
            "code": '''
# Mock 数据库查询
@patch('your_module.database.query')
def test_database_operation(self, mock_query):
    mock_query.return_value = [
        {"id": 1, "name": "测试数据1"},
        {"id": 2, "name": "测试数据2"}
    ]
    
    # 执行测试
    result = your_function()
    self.assertEqual(len(result), 2)
'''
        },
        
        "文件操作Mock": {
            "description": "模拟文件读写",
            "code": '''
# Mock 文件操作
@patch('builtins.open', create=True)
def test_file_operation(self, mock_open):
    mock_file = MagicMock()
    mock_file.read.return_value = "测试文件内容"
    mock_open.return_value.__enter__.return_value = mock_file
    
    # 执行测试
    result = your_function()
    self.assertIn("测试文件内容", result)
'''
        },
        
        "时间Mock": {
            "description": "模拟时间相关操作",
            "code": '''
# Mock 时间
@patch('time.time')
def test_time_operation(self, mock_time):
    mock_time.return_value = 1642492800  # 2022-01-18 00:00:00
    
    # 执行测试
    result = your_function()
    self.assertIsNotNone(result)
'''
        }
    }
    
    return examples


def main():
    """主函数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("🚀 TRAE AI 测试覆盖率分析工具")
    print("=" * 50)
    
    # 分析代码覆盖率
    analyzer = CodeAnalyzer(project_root)
    report = analyzer.scan_project()
    
    # 输出覆盖率报告
    print(f"\n📈 测试覆盖率报告:")
    print(f"总函数数量: {report.total_functions}")
    print(f"已测试函数: {report.tested_functions}")
    print(f"未测试函数: {len(report.untested_functions)}")
    print(f"覆盖率: {report.coverage_percentage:.1f}%")
    
    # 显示未测试的函数
    if report.untested_functions:
        print(f"\n❌ 未测试的函数:")
        for func in report.untested_functions[:10]:  # 只显示前10个
            print(f"  - {func.name} ({func.file_path}:{func.line_number})")
        
        if len(report.untested_functions) > 10:
            print(f"  ... 还有 {len(report.untested_functions) - 10} 个函数")
    
    # 生成缺失的测试用例
    generator = TestCaseGenerator(report)
    missing_tests = generator.generate_missing_tests()
    
    # 保存生成的测试用例
    output_file = os.path.join(project_root, 'tests', 'test_missing_coverage.py')
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(missing_tests)
        print(f"\n✅ 已生成缺失测试用例: {output_file}")
    except Exception as e:
        print(f"\n❌ 生成测试用例失败: {e}")
    
    # 显示Mock数据示例
    print(f"\n🎭 Mock 数据生成示例:")
    examples = generate_mock_data_examples()
    for name, example in examples.items():
        print(f"\n{name}: {example['description']}")
        print(f"```python{example['code']}```")
    
    # 保存详细报告
    report_file = os.path.join(project_root, 'tests', 'coverage_report.json')
    try:
        report_data = {
            "total_functions": report.total_functions,
            "tested_functions": report.tested_functions,
            "coverage_percentage": report.coverage_percentage,
            "untested_functions": [
                {
                    "name": f.name,
                    "file_path": f.file_path,
                    "line_number": f.line_number
                }
                for f in report.untested_functions
            ]
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"\n📊 详细报告已保存: {report_file}")
    except Exception as e:
        print(f"\n❌ 保存报告失败: {e}")


if __name__ == '__main__':
    main()