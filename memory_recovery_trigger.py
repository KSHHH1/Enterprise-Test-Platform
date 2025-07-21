#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI记忆恢复触发系统
当用户说出特定触发词时，自动读取记忆数据库恢复上下文
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from ai_memory_manager import MemoryManager
except ImportError:
    print("❌ 无法导入记忆管理器")
    sys.exit(1)

class MemoryRecoveryTrigger:
    """记忆恢复触发器"""
    
    def __init__(self):
        self.memory = None
        self.trigger_phrases = [
            "恢复记忆"
        ]
        
        # 项目相关触发词
        self.project_triggers = [
            "测试平台",
            "企业测试平台", 
            "Enterprise Test Platform",
            "agent",
            "center_api",
            "MCP",
            "数据库",
            "Flask",
            "设备管理"
        ]
    
    def check_trigger(self, user_input: str) -> bool:
        """检查用户输入是否包含触发词"""
        user_input_lower = user_input.lower()
        
        # 检查直接触发词
        for phrase in self.trigger_phrases:
            if phrase.lower() in user_input_lower:
                return True
        
        # 检查项目相关触发词（需要至少2个）
        project_matches = sum(1 for trigger in self.project_triggers 
                            if trigger.lower() in user_input_lower)
        
        return project_matches >= 2
    
    def initialize_memory(self):
        """初始化记忆管理器"""
        try:
            self.memory = MemoryManager()
            return True
        except Exception as e:
            print(f"❌ 记忆系统初始化失败: {e}")
            return False
    
    def recover_memory(self, user_input: str) -> dict:
        """恢复相关记忆"""
        if not self.memory:
            if not self.initialize_memory():
                return {"status": "error", "message": "记忆系统不可用"}
        
        try:
            # 提取关键词进行搜索
            keywords = self.extract_search_keywords(user_input)
            
            # 搜索相关记忆
            search_results = self.memory.recall(keywords, limit=10)
            
            # 获取最近记忆
            recent_memory = self.memory.db.get_recent_memory(days=30, limit=15)
            
            # 获取项目上下文
            project_context = self.memory.get_context("Enterprise Test Platform")
            
            # 格式化恢复的记忆
            recovery_data = {
                "status": "success",
                "trigger_detected": True,
                "search_keywords": keywords,
                "search_results": search_results,
                "recent_memory": recent_memory,
                "project_context": project_context,
                "summary": self.generate_memory_summary(search_results, recent_memory, project_context)
            }
            
            return recovery_data
            
        except Exception as e:
            return {"status": "error", "message": f"记忆恢复失败: {e}"}
    
    def extract_search_keywords(self, text: str) -> str:
        """从用户输入中提取搜索关键词"""
        import re
        
        # 移除常见停用词
        stop_words = {
            '的', '了', '在', '是', '我', '你', '他', '她', '它', '我们', '你们', '他们',
            '这', '那', '这个', '那个', '什么', '怎么', '为什么', '哪里', '什么时候',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
        }
        
        # 提取有意义的词汇
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return ' '.join(keywords[:10])  # 限制关键词数量
    
    def generate_memory_summary(self, search_results: dict, recent_memory: dict, project_context: dict) -> str:
        """生成记忆摘要"""
        summary_parts = []
        
        # 搜索结果摘要
        if search_results['interactions']:
            summary_parts.append(f"🔍 找到 {len(search_results['interactions'])} 个相关交互记录")
        
        if search_results['knowledge_points']:
            summary_parts.append(f"🧠 找到 {len(search_results['knowledge_points'])} 个相关知识点")
        
        # 最近记忆摘要
        if recent_memory['sessions']:
            summary_parts.append(f"📅 最近 {len(recent_memory['sessions'])} 个会话")
        
        # 项目上下文摘要
        if project_context['sessions']:
            summary_parts.append(f"📁 项目相关 {len(project_context['sessions'])} 个会话")
        
        if project_context['file_changes']:
            summary_parts.append(f"📝 {len(project_context['file_changes'])} 个文件变更记录")
        
        return " | ".join(summary_parts) if summary_parts else "暂无相关记忆"
    
    def format_memory_for_display(self, recovery_data: dict) -> str:
        """格式化记忆数据用于显示"""
        if recovery_data["status"] != "success":
            return f"❌ {recovery_data['message']}"
        
        output = []
        output.append("🧠 记忆恢复成功！")
        output.append("=" * 40)
        output.append(f"📊 摘要: {recovery_data['summary']}")
        output.append("")
        
        # 显示最相关的交互
        interactions = recovery_data['search_results']['interactions']
        if interactions:
            output.append("🔍 最相关的交互记录:")
            for i, interaction in enumerate(interactions[:3], 1):
                output.append(f"{i}. 用户: {interaction['user_input'][:80]}...")
                output.append(f"   AI: {interaction['ai_response'][:80]}...")
                output.append(f"   时间: {interaction['timestamp']}")
                output.append("")
        
        # 显示重要知识点
        knowledge_points = recovery_data['search_results']['knowledge_points']
        if knowledge_points:
            output.append("🧠 相关知识点:")
            for i, kp in enumerate(knowledge_points[:3], 1):
                output.append(f"{i}. {kp['title']}")
                output.append(f"   {kp['content'][:100]}...")
                output.append("")
        
        # 显示最近会话
        recent_sessions = recovery_data['recent_memory']['sessions']
        if recent_sessions:
            output.append("📅 最近会话:")
            for i, session in enumerate(recent_sessions[:3], 1):
                output.append(f"{i}. {session[1]} - {session[2]}")  # session_id, start_time
                if session[4]:  # session_summary
                    output.append(f"   摘要: {session[4][:60]}...")
                output.append("")
        
        return "\n".join(output)

def check_and_recover_memory(user_input: str) -> str:
    """检查触发条件并恢复记忆的主函数"""
    trigger = MemoryRecoveryTrigger()
    
    # 检查是否触发记忆恢复
    if trigger.check_trigger(user_input):
        print("🎯 检测到记忆恢复触发条件")
        recovery_data = trigger.recover_memory(user_input)
        return trigger.format_memory_for_display(recovery_data)
    else:
        return "未检测到记忆恢复触发条件"

def main():
    """主函数 - 提供简单的触发测试"""
    print("🧠 记忆恢复触发系统已就绪")
    print("触发条件:")
    print("1. 直接触发词: 恢复记忆、回忆一下、之前我们聊过等")
    print("2. 项目相关: 包含2个以上项目关键词")
    print("3. 使用方法: check_and_recover_memory(user_input)")

if __name__ == "__main__":
    main()