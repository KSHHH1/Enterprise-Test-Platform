#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI记忆数据库管理系统
用于存储和快速检索AI与用户的交互记忆
"""

import sqlite3
import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

class AIMemoryDatabase:
    """AI记忆数据库管理类"""
    
    def __init__(self, db_path: str = "D:/AI_Memory_Database/ai_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """初始化数据库结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 会话表 - 记录每次对话会话
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    project_context TEXT,
                    session_summary TEXT,
                    total_interactions INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 交互记录表 - 详细的交互内容
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    interaction_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    user_input TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    context_summary TEXT,
                    keywords TEXT,
                    file_operations TEXT,
                    code_changes TEXT,
                    importance_score INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # 知识点表 - 提取的重要知识点
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    tags TEXT,
                    related_files TEXT,
                    source_interaction_id TEXT,
                    importance_score INTEGER DEFAULT 1,
                    access_count INTEGER DEFAULT 0,
                    last_accessed DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_interaction_id) REFERENCES interactions(interaction_id)
                )
            ''')
            
            # 文件变更记录表 - 跟踪文件修改历史
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    change_id TEXT UNIQUE NOT NULL,
                    session_id TEXT NOT NULL,
                    interaction_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    change_summary TEXT,
                    before_content TEXT,
                    after_content TEXT,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (interaction_id) REFERENCES interactions(interaction_id)
                )
            ''')
            
            # 快速检索索引表 - 用于快速搜索
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    content_snippet TEXT,
                    relevance_score REAL DEFAULT 1.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引以提高查询性能
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time)",
                "CREATE INDEX IF NOT EXISTS idx_interactions_session_id ON interactions(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_interactions_keywords ON interactions(keywords)",
                "CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_points(category)",
                "CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_points(tags)",
                "CREATE INDEX IF NOT EXISTS idx_knowledge_importance ON knowledge_points(importance_score)",
                "CREATE INDEX IF NOT EXISTS idx_file_changes_path ON file_changes(file_path)",
                "CREATE INDEX IF NOT EXISTS idx_search_keywords ON search_index(keywords)",
                "CREATE INDEX IF NOT EXISTS idx_search_relevance ON search_index(relevance_score)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
        
        print(f"✅ AI记忆数据库初始化完成: {self.db_path}")
    
    def generate_id(self, content: str) -> str:
        """生成唯一ID"""
        return hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:16]
    
    def start_session(self, project_context: str = "") -> str:
        """开始新的会话"""
        session_id = self.generate_id(f"session_{datetime.now().isoformat()}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (session_id, start_time, project_context)
                VALUES (?, ?, ?)
            ''', (session_id, datetime.now(), project_context))
            conn.commit()
        
        print(f"🚀 新会话开始: {session_id}")
        return session_id
    
    def end_session(self, session_id: str, session_summary: str = ""):
        """结束会话"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 统计交互次数
            cursor.execute('''
                SELECT COUNT(*) FROM interactions WHERE session_id = ?
            ''', (session_id,))
            total_interactions = cursor.fetchone()[0]
            
            cursor.execute('''
                UPDATE sessions 
                SET end_time = ?, session_summary = ?, total_interactions = ?
                WHERE session_id = ?
            ''', (datetime.now(), session_summary, total_interactions, session_id))
            
            conn.commit()
        
        print(f"🏁 会话结束: {session_id}, 总交互次数: {total_interactions}")
    
    def record_interaction(self, session_id: str, user_input: str, ai_response: str, 
                          context_summary: str = "", file_operations: List[Dict] = None,
                          code_changes: List[Dict] = None, importance_score: int = 1) -> str:
        """记录交互内容"""
        interaction_id = self.generate_id(f"interaction_{user_input[:50]}")
        
        # 提取关键词
        keywords = self.extract_keywords(user_input + " " + ai_response)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO interactions (
                    session_id, interaction_id, timestamp, user_input, ai_response,
                    context_summary, keywords, file_operations, code_changes, importance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, interaction_id, datetime.now(), user_input, ai_response,
                context_summary, keywords, json.dumps(file_operations or []),
                json.dumps(code_changes or []), importance_score
            ))
            conn.commit()
        
        # 更新搜索索引
        self.update_search_index("interaction", interaction_id, keywords, 
                               user_input[:200] + "..." if len(user_input) > 200 else user_input)
        
        print(f"📝 交互记录已保存: {interaction_id}")
        return interaction_id
    
    def add_knowledge_point(self, title: str, content: str, category: str = "",
                           tags: List[str] = None, related_files: List[str] = None,
                           source_interaction_id: str = "", importance_score: int = 1) -> str:
        """添加知识点"""
        knowledge_id = self.generate_id(f"knowledge_{title}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO knowledge_points (
                    knowledge_id, title, content, category, tags, related_files,
                    source_interaction_id, importance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                knowledge_id, title, content, category, 
                json.dumps(tags or []), json.dumps(related_files or []),
                source_interaction_id, importance_score
            ))
            conn.commit()
        
        # 更新搜索索引
        keywords = self.extract_keywords(title + " " + content + " " + " ".join(tags or []))
        self.update_search_index("knowledge", knowledge_id, keywords, content[:200])
        
        print(f"🧠 知识点已添加: {title}")
        return knowledge_id
    
    def record_file_change(self, session_id: str, interaction_id: str, file_path: str,
                          operation_type: str, change_summary: str = "",
                          before_content: str = "", after_content: str = "") -> str:
        """记录文件变更"""
        change_id = self.generate_id(f"change_{file_path}_{operation_type}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO file_changes (
                    change_id, session_id, interaction_id, file_path, operation_type,
                    change_summary, before_content, after_content, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                change_id, session_id, interaction_id, file_path, operation_type,
                change_summary, before_content, after_content, datetime.now()
            ))
            conn.commit()
        
        print(f"📁 文件变更已记录: {file_path} ({operation_type})")
        return change_id
    
    def extract_keywords(self, text: str) -> str:
        """提取关键词"""
        # 简单的关键词提取逻辑
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 过滤常见停用词
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'this', 'that', 'these', 'those', 'here', 'there', 'where', 'when', 'why', 'how',
            '的', '了', '在', '是', '我', '你', '他', '她', '它', '我们', '你们', '他们',
            '这', '那', '这个', '那个', '什么', '怎么', '为什么', '哪里', '什么时候'
        }
        
        # 过滤停用词并保留长度大于2的词
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # 去重并限制数量
        unique_keywords = list(set(keywords))[:20]
        
        return " ".join(unique_keywords)
    
    def update_search_index(self, content_type: str, content_id: str, keywords: str, snippet: str):
        """更新搜索索引"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO search_index (content_type, content_id, keywords, content_snippet)
                VALUES (?, ?, ?, ?)
            ''', (content_type, content_id, keywords, snippet))
            conn.commit()
    
    def search_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索记忆内容"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 搜索交互记录
            cursor.execute('''
                SELECT i.*, s.project_context
                FROM interactions i
                JOIN sessions s ON i.session_id = s.session_id
                WHERE i.keywords LIKE ? OR i.user_input LIKE ? OR i.ai_response LIKE ?
                ORDER BY i.importance_score DESC, i.timestamp DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            interactions = cursor.fetchall()
            interaction_columns = [description[0] for description in cursor.description]
            
            # 搜索知识点
            cursor.execute('''
                SELECT * FROM knowledge_points
                WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
                ORDER BY importance_score DESC, access_count DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            knowledge_points = cursor.fetchall()
            knowledge_columns = [description[0] for description in cursor.description]
        
        results = {
            'interactions': [dict(zip(interaction_columns, row)) for row in interactions],
            'knowledge_points': [dict(zip(knowledge_columns, row)) for row in knowledge_points]
        }
        
        print(f"🔍 搜索完成: 找到 {len(interactions)} 个交互记录, {len(knowledge_points)} 个知识点")
        return results
    
    def get_recent_memory(self, days: int = 7, limit: int = 20) -> Dict:
        """获取最近的记忆"""
        since_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 最近的会话
            cursor.execute('''
                SELECT * FROM sessions
                WHERE start_time >= ?
                ORDER BY start_time DESC
                LIMIT ?
            ''', (since_date, limit))
            
            sessions = cursor.fetchall()
            
            # 最近的重要交互
            cursor.execute('''
                SELECT * FROM interactions
                WHERE timestamp >= ? AND importance_score >= 3
                ORDER BY importance_score DESC, timestamp DESC
                LIMIT ?
            ''', (since_date, limit))
            
            important_interactions = cursor.fetchall()
            
            # 最近访问的知识点
            cursor.execute('''
                SELECT * FROM knowledge_points
                WHERE last_accessed >= ? OR created_at >= ?
                ORDER BY importance_score DESC, access_count DESC
                LIMIT ?
            ''', (since_date, since_date, limit))
            
            knowledge_points = cursor.fetchall()
        
        return {
            'sessions': sessions,
            'important_interactions': important_interactions,
            'knowledge_points': knowledge_points
        }
    
    def get_project_context(self, project_name: str = "Enterprise Test Platform") -> Dict:
        """获取特定项目的上下文记忆"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 项目相关的会话
            cursor.execute('''
                SELECT * FROM sessions
                WHERE project_context LIKE ?
                ORDER BY start_time DESC
                LIMIT 10
            ''', (f'%{project_name}%',))
            
            sessions = cursor.fetchall()
            
            # 项目相关的文件变更
            cursor.execute('''
                SELECT * FROM file_changes
                WHERE file_path LIKE ?
                ORDER BY timestamp DESC
                LIMIT 20
            ''', (f'%{project_name}%',))
            
            file_changes = cursor.fetchall()
            
            # 项目相关的知识点
            cursor.execute('''
                SELECT * FROM knowledge_points
                WHERE content LIKE ? OR related_files LIKE ?
                ORDER BY importance_score DESC
                LIMIT 15
            ''', (f'%{project_name}%', f'%{project_name}%'))
            
            knowledge_points = cursor.fetchall()
        
        return {
            'sessions': sessions,
            'file_changes': file_changes,
            'knowledge_points': knowledge_points
        }
    
    def optimize_database(self):
        """优化数据库性能"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 清理旧的搜索索引
            cursor.execute('''
                DELETE FROM search_index 
                WHERE created_at < datetime('now', '-30 days')
            ''')
            
            # 更新知识点访问统计
            cursor.execute('''
                UPDATE knowledge_points 
                SET last_accessed = datetime('now')
                WHERE access_count > 0
            ''')
            
            # 重建索引
            cursor.execute('REINDEX')
            
            # 分析表以优化查询计划
            cursor.execute('ANALYZE')
            
            conn.commit()
        
        print("🔧 数据库优化完成")
    
    def export_memory_summary(self, output_path: str = None) -> str:
        """导出记忆摘要"""
        if not output_path:
            output_path = f"D:/AI_Memory_Database/memory_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取统计信息
            cursor.execute('SELECT COUNT(*) FROM sessions')
            total_sessions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM interactions')
            total_interactions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM knowledge_points')
            total_knowledge = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM file_changes')
            total_file_changes = cursor.fetchone()[0]
            
            # 获取最重要的知识点
            cursor.execute('''
                SELECT title, content, importance_score, access_count
                FROM knowledge_points
                ORDER BY importance_score DESC, access_count DESC
                LIMIT 20
            ''')
            top_knowledge = cursor.fetchall()
        
        summary = {
            'export_time': datetime.now().isoformat(),
            'statistics': {
                'total_sessions': total_sessions,
                'total_interactions': total_interactions,
                'total_knowledge_points': total_knowledge,
                'total_file_changes': total_file_changes
            },
            'top_knowledge_points': [
                {
                    'title': row[0],
                    'content': row[1][:200] + '...' if len(row[1]) > 200 else row[1],
                    'importance_score': row[2],
                    'access_count': row[3]
                }
                for row in top_knowledge
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"📊 记忆摘要已导出: {output_path}")
        return output_path

# 简化的记忆管理接口
class MemoryManager:
    """简化的记忆管理接口"""
    
    def __init__(self):
        self.db = AIMemoryDatabase()
        self.current_session_id = None
    
    def start_new_session(self, project_context: str = "Enterprise Test Platform"):
        """开始新会话"""
        self.current_session_id = self.db.start_session(project_context)
        return self.current_session_id
    
    def remember(self, user_input: str, ai_response: str, importance: int = 1):
        """记住一次交互"""
        if not self.current_session_id:
            self.start_new_session()
        
        return self.db.record_interaction(
            self.current_session_id, user_input, ai_response, 
            importance_score=importance
        )
    
    def recall(self, query: str, limit: int = 5):
        """回忆相关内容"""
        return self.db.search_memory(query, limit)
    
    def get_context(self, project: str = "Enterprise Test Platform"):
        """获取项目上下文"""
        return self.db.get_project_context(project)
    
    def end_session(self, summary: str = ""):
        """结束当前会话"""
        if self.current_session_id:
            self.db.end_session(self.current_session_id, summary)
            self.current_session_id = None

def main():
    """主函数 - 初始化数据库"""
    print("🧠 AI记忆数据库系统初始化")
    print("=" * 40)
    
    # 初始化数据库
    memory = MemoryManager()
    
    print(f"✅ 数据库初始化完成: {memory.db.db_path}")
    print("\n🎯 使用方法:")
    print("1. 导入: from ai_memory_manager import MemoryManager")
    print("2. 初始化: memory = MemoryManager()")
    print("3. 记忆: memory.remember(user_input, ai_response, importance)")
    print("4. 回忆: results = memory.recall(query)")
    print("5. 上下文: context = memory.get_context(project)")

if __name__ == "__main__":
    main()