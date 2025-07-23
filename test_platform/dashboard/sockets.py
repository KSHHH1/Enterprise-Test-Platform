from flask_socketio import emit
from flask import session, current_app
import time

# 注意：socketio实例将在app.py中初始化后导入
socketio = None

def init_socketio(app_socketio):
    """初始化socketio实例"""
    global socketio
    socketio = app_socketio

# 可以在这里定义与仪表盘相关的WebSocket事件处理器

def handle_connect():
    """
    处理客户端连接事件。
    可以在这里进行用户认证或会话设置。
    """
    current_app.logger.info(f"Client connected: {session.sid}")
    emit('response', {'data': 'Connected', 'sid': session.sid})

def handle_disconnect():
    """处理客户端断开连接事件。"""
    current_app.logger.info(f"Client disconnected: {session.sid}")

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

def default_error_handler(e):
    """默认的错误处理器。"""
    current_app.logger.error(f"Socket.IO Error: {e}")
    emit('error', {'error': str(e)})

def handle_host_status_change(data):
    """处理主机状态变更，并广播给所有客户端"""
    emit('host_status_update', data, broadcast=True)

def handle_subscribe_alerts(data):
    """处理客户端订阅告警事件"""
    current_app.logger.info(f"Client {session.sid} subscribed to alerts")
    emit('alert_subscription_confirmed', {'status': 'subscribed'})

def handle_unsubscribe_alerts(data):
    """处理客户端取消订阅告警事件"""
    current_app.logger.info(f"Client {session.sid} unsubscribed from alerts")
    emit('alert_subscription_confirmed', {'status': 'unsubscribed'})

def handle_acknowledge_alert(data):
    """处理客户端确认告警事件"""
    try:
        alert_id = data.get('alert_id')
        if alert_id:
            # 这里可以调用告警服务来确认告警
            current_app.logger.info(f"Client {session.sid} acknowledged alert {alert_id}")
            emit('alert_acknowledged', {'alert_id': alert_id, 'status': 'success'})
        else:
            emit('alert_acknowledged', {'error': 'Missing alert_id'})
    except Exception as e:
        current_app.logger.error(f"Error acknowledging alert: {str(e)}")
        emit('alert_acknowledged', {'error': str(e)})

def register_socketio_events(socketio_instance):
    """注册所有socketio事件处理器"""
    global socketio
    socketio = socketio_instance
    
    socketio.on_event('connect', handle_connect)
    socketio.on_event('disconnect', handle_disconnect)
    socketio.on_event('request_server_info', handle_server_info)
    socketio.on_event('host_status_changed', handle_host_status_change)
    socketio.on_event('subscribe_alerts', handle_subscribe_alerts)
    socketio.on_event('unsubscribe_alerts', handle_unsubscribe_alerts)
    socketio.on_event('acknowledge_alert', handle_acknowledge_alert)
    socketio.on_error_default(default_error_handler)