# Enterprise Test Platform

## 🎯 项目概述

Enterprise Test Platform 是一个企业级测试平台，集成了AI记忆系统、MCP服务、设备管理和自动化测试功能。该平台提供了完整的测试解决方案，支持多种设备接入、智能化测试流程和数据分析。

## ✨ 核心功能

### 🧠 AI记忆系统
- **智能记忆存储**: 自动保存重要对话和知识点
- **快速记忆恢复**: 通过触发词快速恢复历史记忆
- **上下文关联**: 智能关联项目相关信息
- **知识点管理**: 结构化存储技术要点和解决方案

### 🔧 MCP集成服务
- **多协议支持**: 支持多种MCP协议和服务
- **实时通信**: WebSocket实时数据传输
- **API接口**: RESTful API设计
- **服务发现**: 自动服务注册和发现

### 🖥️ 设备管理
- **多设备支持**: 支持串口、网络等多种设备接入
- **状态监控**: 实时设备状态监控
- **自动化控制**: 设备自动化操作和测试
- **数据采集**: 设备数据实时采集和分析

### 🌐 Web界面
- **现代化UI**: 基于Flask的现代化Web界面
- **实时仪表板**: 实时数据展示和监控
- **用户认证**: 完整的用户认证和权限管理
- **响应式设计**: 支持多种设备访问

## 🚀 快速开始

### 环境要求
- Python 3.8+
- SQLite 3
- 现代浏览器

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动服务
```bash
# 启动主服务
python manage.py

# 启动Web界面
python test_platform/app.py

# 启动Agent服务
python new_agent.py
```

### Docker部署
```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose-production.yml up -d
```

## 📁 项目结构

```
Enterprise Test Platform/
├── enterprise_platform/          # 核心平台代码
│   ├── api/                      # API接口
│   ├── config/                   # 配置管理
│   ├── core/                     # 核心功能
│   └── utils/                    # 工具函数
├── test_platform/               # Web测试平台
│   ├── auth/                    # 用户认证
│   ├── core/                    # 核心路由
│   ├── dashboard/               # 仪表板
│   └── static/                  # 静态资源
├── ai_memory_manager.py         # AI记忆管理
├── memory_recovery_trigger.py   # 记忆恢复触发器
├── memory_save_trigger.py       # 记忆保存触发器
├── center_api.py               # 中心API服务
├── new_agent.py                # Agent服务
└── requirements.txt            # 依赖包列表
```

## 🧠 AI记忆系统使用

### 记忆恢复
在对话中直接说出触发词：
- "恢复记忆"
- "回忆一下"
- "之前我们聊过"

### 记忆保存
在对话中说出保存触发词：
- "记录记忆"
- "保存记忆"
- "存储记忆"

### 数据库位置
```
D:\AI_Memory_Database\ai_memory.db
```

## 🔧 配置说明

### 基础配置
- 修改 `enterprise_platform/config/settings.py` 进行基础配置
- 网络配置参考 `网络访问配置.md`
- 防火墙设置运行 `setup_firewall.bat`

### 服务配置
- Agent配置: `new_agent.py`
- API配置: `center_api.py`
- Web配置: `test_platform/app.py`

## 📊 监控和日志

### 日志文件
- 系统日志: `logs/enterprise_platform.*.log`
- Agent日志: `logs/agent_startup.log`
- API日志: `logs/center_startup.log`

### 监控面板
访问 Web界面查看实时监控数据和系统状态。

## 🔒 安全特性

- 用户认证和授权
- API访问控制
- 数据加密传输
- 防火墙配置
- VPN访问支持

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 开发日志

详细的开发记录请查看 `开发日志/` 目录：
- [AI接入方案](开发日志/AI接入方案_2025-01-19.md)
- [MCP集成报告](开发日志/MCP集成完成报告_2025-01-19.md)
- [开发计划](开发日志/开发计划_2025-01-19.md)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 创建 Issue
- 发送 Pull Request
- 查看项目文档

---

⭐ 如果这个项目对你有帮助，请给它一个星标！