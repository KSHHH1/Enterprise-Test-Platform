from ..app import socketio
from flask_socketio import emit
from flask import session, current_app
import time

# 可以在这里定义与仪表盘相关的WebSocket事件处理器

@socketio.on('connect')
def handle_connect():
    """
    处理客户端连接事件。
    可以在这里进行用户认证或会话设置。
    """
    current_app.logger.info(f"Client connected: {session.sid}")
    emit('response', {'data': 'Connected', 'sid': session.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接事件。"""
    current_app.logger.info(f"Client disconnected: {session.sid}")

@socketio.on('request_server_info')
def handle_server_info(message):
    """
    一个示例事件，用于客户端请求服务器信息。
    """
    current_app.logger.info(f"Received server info request from {session.sid} with data: {message}")
    
    # 模拟一个耗时任务，并逐步返回信息
    for i in range(5):
        time.sleep(1)
        emit('server_info_update', {'progress': (i + 1) * 20, 'message': f'Processing step {i+1}...'})
    
    emit('server_info_update', {'progress': 100, 'message': 'Done!', 'final': True})

@socketio.on_error_default
def default_error_handler(e):
    """默认的错误处理器。"""
    current_app.logger.error(f"Socket.IO Error: {e}")
    emit('error', {'error': str(e)})


@socketio.on('host_status_changed')
def handle_host_status_change(data):
    """处理主机状态变更，并广播给所有客户端"""
    emit('host_status_update', data, broadcast=True)