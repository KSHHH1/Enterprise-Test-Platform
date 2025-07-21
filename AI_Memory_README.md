# AI记忆数据库系统

## 概述
这是一个专为AI助理设计的记忆数据库系统，用于存储和快速检索与用户的交互内容，实现记忆恢复功能。

## 特性
- 🧠 **智能记忆存储**: 自动记录用户交互和AI响应
- 🔍 **快速检索**: 基于关键词的高效搜索
- 📊 **知识点管理**: 提取和存储重要知识点
- 📁 **文件变更跟踪**: 记录代码修改历史
- 🎯 **项目上下文**: 按项目组织记忆内容
- ⚡ **性能优化**: 索引优化，支持大量数据快速读取

## 数据库结构
- **sessions**: 会话管理
- **interactions**: 交互记录
- **knowledge_points**: 知识点存储
- **file_changes**: 文件变更记录
- **search_index**: 搜索索引

## 使用方法

### 基本使用
```python
from ai_memory_manager import MemoryManager

# 初始化记忆管理器
memory = MemoryManager()

# 开始新会话
session_id = memory.start_new_session("项目名称")

# 记录交互 (重要程度: 1-5)
memory.remember(
    user_input="用户输入内容",
    ai_response="AI回复内容", 
    importance=3
)

# 搜索相关记忆
results = memory.recall("搜索关键词")

# 获取项目上下文
context = memory.get_context("项目名称")

# 结束会话
memory.end_session("会话总结")
```

### 高级功能
```python
# 添加知识点
memory.db.add_knowledge_point(
    title="知识点标题",
    content="详细内容",
    category="分类",
    tags=["标签1", "标签2"],
    importance_score=4
)

# 记录文件变更
memory.db.record_file_change(
    session_id=session_id,
    interaction_id=interaction_id,
    file_path="文件路径",
    operation_type="create/update/delete",
    change_summary="变更说明"
)

# 数据库优化
memory.db.optimize_database()

# 导出记忆摘要
summary_path = memory.db.export_memory_summary()
```

## 文件位置
- **数据库文件**: `D:/AI_Memory_Database/ai_memory.db`
- **摘要报告**: `D:/AI_Memory_Database/memory_summary_*.json`

## 性能优化
- 使用SQLite索引加速查询
- 关键词提取和搜索索引
- 定期数据库优化和清理
- 分页查询避免内存溢出

## 注意事项
- 数据库会自动创建在D盘
- 支持并发访问，使用连接池
- 定期执行数据库优化以保持性能
- 重要交互建议设置较高的重要程度分数