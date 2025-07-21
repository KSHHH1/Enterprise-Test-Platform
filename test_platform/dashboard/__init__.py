from flask import Blueprint

# 仪表盘蓝图，未来可以添加与仪表盘相关的API路由
bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

# 移除对已删除的routes.py的导入
# from . import routes, events
from . import events 