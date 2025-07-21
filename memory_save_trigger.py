#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI记忆保存触发系统
当用户说出"记录记忆"时，自动精简并保存对话内容到数据库
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from ai_memory_manager import MemoryManager
except ImportError:
    print("❌ 无法导入记忆管理器")
    sys.exit(1)

class MemorySaveTrigger:
    """记忆保存触发器"""
    
    def __init__(self):
        self.memory = None
        self.save_trigger_phrases = [
            "记录记忆",
            "保存记忆", 
            "存储记忆",
            "记住这次对话"
        ]
        
        # 对话历史缓存
        self.conversation_history = []
        
    def check_save_trigger(self, user_input: str) -> bool:
        """检查用户输入是否包含保存触发词"""
        user_input_lower = user_input.lower()
        
        for phrase in self.save_trigger_phrases:
            if phrase.lower() in user_input_lower:
                return True
        
        return False
    
    def initialize_memory(self):
        """初始化记忆管理器"""
        try:
            self.memory = MemoryManager()
            return True
        except Exception as e:
            print(f"❌ 记忆系统初始化失败: {e}")
            return False
    
    def add_conversation_turn(self, user_input: str, ai_response: str):
        """添加一轮对话到历史记录"""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'ai_response': ai_response
        })
        
        # 保持最近50轮对话
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def summarize_conversation(self, conversation_turns: List[Dict]) -> Dict[str, Any]:
        """精简对话内容，提取关键信息"""
        if not conversation_turns:
            return {
                'summary': '无对话内容',
                'key_topics': [],
                'important_points': [],
                'file_operations': [],
                'code_changes': [],
                'total_turns': 0,
                'time_span': ''
            }
        
        # 提取关键主题
        key_topics = self.extract_key_topics(conversation_turns)
        
        # 提取重要观点
        important_points = self.extract_important_points(conversation_turns)
        
        # 提取文件操作
        file_operations = self.extract_file_operations(conversation_turns)
        
        # 提取代码变更
        code_changes = self.extract_code_changes(conversation_turns)
        
        # 生成对话摘要
        summary = self.generate_conversation_summary(
            conversation_turns, key_topics, important_points
        )
        
        # 计算时间跨度
        time_span = ''
        if len(conversation_turns) > 1:
            time_span = f"{conversation_turns[0]['timestamp']} 到 {conversation_turns[-1]['timestamp']}"
        elif len(conversation_turns) == 1:
            time_span = conversation_turns[0]['timestamp']
        
        return {
            'summary': summary,
            'key_topics': key_topics,
            'important_points': important_points,
            'file_operations': file_operations,
            'code_changes': code_changes,
            'total_turns': len(conversation_turns),
            'time_span': time_span
        }
    
    def extract_key_topics(self, conversation_turns: List[Dict]) -> List[str]:
        """提取对话中的关键主题"""
        topics = set()
        
        # 技术关键词
        tech_keywords = [
            'python', 'javascript', 'html', 'css', 'sql', 'api', 'database', 'server',
            'flask', 'django', 'react', 'vue', 'docker', 'git', 'github',
            '数据库', '服务器', '接口', '前端', '后端', '测试', '部署', '配置',
            'agent', 'mcp', '记忆系统', '触发器', '企业测试平台'
        ]
        
        for turn in conversation_turns:
            text = (turn['user_input'] + ' ' + turn['ai_response']).lower()
            
            for keyword in tech_keywords:
                if keyword.lower() in text:
                    topics.add(keyword)
        
        return list(topics)[:10]  # 限制主题数量
    
    def extract_important_points(self, conversation_turns: List[Dict]) -> List[str]:
        """提取重要观点和结论"""
        important_points = []
        
        # 寻找包含重要信息的句子
        important_patterns = [
            r'解决方案[是：](.+)',
            r'问题[是：](.+)',
            r'结论[是：](.+)',
            r'建议(.+)',
            r'注意(.+)',
            r'重要[的是：](.+)',
            r'关键[是：](.+)',
            r'总结(.+)',
            r'实现了(.+)',
            r'修复了(.+)',
            r'添加了(.+)',
            r'创建了(.+)'
        ]
        
        for turn in conversation_turns:
            ai_response = turn['ai_response']
            
            for pattern in important_patterns:
                matches = re.findall(pattern, ai_response, re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 10:  # 过滤太短的内容
                        important_points.append(match.strip()[:100])
        
        return important_points[:10]  # 限制数量
    
    def extract_file_operations(self, conversation_turns: List[Dict]) -> List[Dict]:
        """提取文件操作信息"""
        file_operations = []
        
        file_patterns = [
            r'创建[了]?文件[：:]?\s*([^\s]+)',
            r'修改[了]?文件[：:]?\s*([^\s]+)',
            r'删除[了]?文件[：:]?\s*([^\s]+)',
            r'编辑[了]?[：:]?\s*([^\s]+\.py|[^\s]+\.js|[^\s]+\.html|[^\s]+\.css|[^\s]+\.md)',
            r'保存[到了]?[：:]?\s*([^\s]+\.[a-zA-Z]+)'
        ]
        
        for turn in conversation_turns:
            ai_response = turn['ai_response']
            
            for pattern in file_patterns:
                matches = re.findall(pattern, ai_response, re.IGNORECASE)
                for match in matches:
                    file_operations.append({
                        'file_path': match,
                        'timestamp': turn['timestamp'],
                        'operation': '文件操作'
                    })
        
        return file_operations[:20]  # 限制数量
    
    def extract_code_changes(self, conversation_turns: List[Dict]) -> List[Dict]:
        """提取代码变更信息"""
        code_changes = []
        
        for turn in conversation_turns:
            ai_response = turn['ai_response']
            
            # 检测代码块
            code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', ai_response, re.DOTALL)
            
            for lang, code in code_blocks:
                if len(code.strip()) > 20:  # 过滤太短的代码
                    code_changes.append({
                        'language': lang or 'unknown',
                        'code_snippet': code.strip()[:200] + '...' if len(code) > 200 else code.strip(),
                        'timestamp': turn['timestamp']
                    })
        
        return code_changes[:10]  # 限制数量
    
    def generate_conversation_summary(self, conversation_turns: List[Dict], 
                                    key_topics: List[str], important_points: List[str]) -> str:
        """生成对话摘要"""
        summary_parts = []
        
        # 基本信息
        summary_parts.append(f"对话轮数: {len(conversation_turns)}")
        
        # 主要主题
        if key_topics:
            summary_parts.append(f"主要主题: {', '.join(key_topics[:5])}")
        
        # 重要内容概述
        if important_points:
            summary_parts.append(f"关键内容: {important_points[0][:50]}...")
        
        # 时间范围
        if len(conversation_turns) > 1:
            start_time = conversation_turns[0]['timestamp'][:16]  # 只取日期和小时分钟
            end_time = conversation_turns[-1]['timestamp'][:16]
            summary_parts.append(f"时间: {start_time} - {end_time}")
        
        return " | ".join(summary_parts)
    
    def save_conversation_memory(self, user_input: str) -> Dict[str, Any]:
        """保存对话记忆到数据库"""
        if not self.memory:
            if not self.initialize_memory():
                return {"status": "error", "message": "记忆系统不可用"}
        
        try:
            # 精简对话内容
            conversation_summary = self.summarize_conversation(self.conversation_history)
            
            # 开始新会话（如果还没有）
            if not self.memory.current_session_id:
                session_id = self.memory.start_new_session("Enterprise Test Platform - 记忆保存")
            else:
                session_id = self.memory.current_session_id
            
            # 保存精简后的对话内容
            interaction_id = self.memory.remember(
                user_input=f"记录记忆请求 - 包含{conversation_summary['total_turns']}轮对话",
                ai_response=f"已保存对话记忆: {conversation_summary['summary']}",
                importance=3  # 高重要性
            )
            
            # 保存关键知识点
            knowledge_points_saved = 0
            for i, point in enumerate(conversation_summary['important_points'][:5]):
                knowledge_id = self.memory.db.add_knowledge_point(
                    title=f"对话要点 {i+1}",
                    content=point,
                    category="对话记录",
                    tags=conversation_summary['key_topics'][:3],
                    source_interaction_id=interaction_id,
                    importance_score=2
                )
                knowledge_points_saved += 1
            
            # 记录文件操作
            file_changes_saved = 0
            for file_op in conversation_summary['file_operations'][:10]:
                change_id = self.memory.db.record_file_change(
                    session_id=session_id,
                    interaction_id=interaction_id,
                    file_path=file_op['file_path'],
                    operation_type=file_op['operation'],
                    change_summary=f"对话中提到的文件操作"
                )
                file_changes_saved += 1
            
            # 清空对话历史（已保存）
            saved_turns = len(self.conversation_history)
            self.conversation_history = []
            
            return {
                "status": "success",
                "message": "对话记忆保存成功",
                "details": {
                    "session_id": session_id,
                    "interaction_id": interaction_id,
                    "conversation_turns_saved": saved_turns,
                    "knowledge_points_saved": knowledge_points_saved,
                    "file_changes_saved": file_changes_saved,
                    "summary": conversation_summary['summary'],
                    "key_topics": conversation_summary['key_topics']
                }
            }
            
        except Exception as e:
            return {"status": "error", "message": f"保存记忆失败: {e}"}
    
    def format_save_result(self, save_result: Dict[str, Any]) -> str:
        """格式化保存结果用于显示"""
        if save_result["status"] != "success":
            return f"❌ {save_result['message']}"
        
        details = save_result['details']
        output = []
        output.append("💾 对话记忆保存成功！")
        output.append("=" * 40)
        output.append(f"📊 保存统计:")
        output.append(f"   • 对话轮数: {details['conversation_turns_saved']}")
        output.append(f"   • 知识点: {details['knowledge_points_saved']}")
        output.append(f"   • 文件操作: {details['file_changes_saved']}")
        output.append("")
        output.append(f"📝 对话摘要: {details['summary']}")
        output.append("")
        if details['key_topics']:
            output.append(f"🏷️ 主要主题: {', '.join(details['key_topics'])}")
        output.append("")
        output.append(f"🆔 会话ID: {details['session_id']}")
        output.append(f"🔗 交互ID: {details['interaction_id']}")
        
        return "\n".join(output)

def check_and_save_memory(user_input: str, ai_response: str = "") -> str:
    """检查保存触发条件并保存记忆的主函数"""
    # 全局触发器实例（保持对话历史）
    if not hasattr(check_and_save_memory, 'trigger'):
        check_and_save_memory.trigger = MemorySaveTrigger()
    
    trigger = check_and_save_memory.trigger
    
    # 添加当前对话到历史
    if ai_response:
        trigger.add_conversation_turn(user_input, ai_response)
    
    # 检查是否触发记忆保存
    if trigger.check_save_trigger(user_input):
        print("💾 检测到记忆保存触发条件")
        save_result = trigger.save_conversation_memory(user_input)
        return trigger.format_save_result(save_result)
    else:
        return "未检测到记忆保存触发条件"

def main():
    """主函数 - 提供简单的保存测试"""
    print("💾 记忆保存触发系统已就绪")
    print("触发词: 记录记忆, 保存记忆, 存储记忆, 记住这次对话")
    
    # 测试用例
    test_conversations = [
        ("你好，我想了解这个项目", "你好！这是Enterprise Test Platform项目..."),
        ("如何配置agent", "agent配置需要修改config文件..."),
        ("记录记忆", "")
    ]
    
    for user_input, ai_response in test_conversations:
        result = check_and_save_memory(user_input, ai_response)
        if "检测到记忆保存触发条件" in result or "未检测到" not in result:
            print(result)

if __name__ == "__main__":
    main()