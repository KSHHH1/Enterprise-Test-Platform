#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局AI记忆保存系统
从任何目录都可以调用的记忆保存功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_path = Path("d:/Enterprise Test Platform")
sys.path.insert(0, str(project_path))

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("❌ 使用方法: python global_memory_save.py '用户输入' ['AI回复']")
        print("💡 示例: python global_memory_save.py '记录记忆'")
        return
    
    user_input = sys.argv[1]
    ai_response = sys.argv[2] if len(sys.argv) > 2 else ""
    
    try:
        # 导入记忆保存触发器
        from memory_save_trigger import check_and_save_memory
        
        print(f"🧠 全局AI记忆保存系统")
        print(f"📍 数据库位置: D:/AI_Memory_Database/ai_memory.db")
        print("=" * 50)
        
        # 检查并保存记忆
        result = check_and_save_memory(user_input, ai_response)
        print(result)
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保项目路径正确: d:/Enterprise Test Platform")
    except Exception as e:
        print(f"❌ 执行失败: {e}")

if __name__ == "__main__":
    main()