import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from database import db
from models.device import Device
import secrets

def register_new_device(data):
    """
    根据提供的设备指纹和用户信息注册一个新设备。
    """
    fingerprint = data.get('fingerprint')
    if not fingerprint:
        raise ValueError("Device fingerprint is required for registration.")

    # 自动生成设备名和密码
    user_agent_string = request.headers.get('User-Agent', 'Unknown Agent')
    ip_address = request.remote_addr
    device_name = f"Device from {ip_address}" 
    password = secrets.token_hex(8) # 生成一个随机密码

    new_device = Device(
        fingerprint=fingerprint,
        name=device_name,
        registered_ip=ip_address,
        user_agent=user_agent_string,
        password_hash=password # 注意：在实际生产中, 应存储哈希值
    )
    db.session.add(new_device)
    db.session.commit()
    return password

def authenticate_device(data):
    """
    验证设备密码, 成功则返回JWT和设备信息.
    """
    password = data.get('password')
    fingerprint = data.get('fingerprint')

    if not password or not fingerprint:
        return None, None
        
    # 简化版：直接对比明文密码。生产环境应使用哈希校验。
    device = Device.query.filter_by(fingerprint=fingerprint).first()
    if not device:
        if password == current_app.config.get('SHARED_PASSWORD'):
            # 自动注册
            new_device = Device(
                fingerprint=fingerprint,
                name=f'Device_{fingerprint[:8]}',  # 简单名称
                registered_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent', 'Unknown'),
                password_hash=password  # 暂存明文，生产中应哈希
            )
            db.session.add(new_device)
            db.session.commit()
            token = create_token(new_device)
            return token, new_device
        else:
            return None, None
    # 现有设备验证
    if device.password_hash == password:
        device.last_login_at = datetime.utcnow()
        db.session.commit()
        token = create_token(device)
        return token, device
    return None, None

def create_token(device):
    """为指定设备创建JWT."""
    token = jwt.encode({
        'device_id': device.id,
        'fingerprint': device.fingerprint,
        'name': device.name,
        'exp': datetime.utcnow() + timedelta(hours=24 * 30)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")
    return token

def token_required(f):
    """Token验证装饰器（简化版，不再创建闭包）."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_device = Device.query.get(data['device_id'])
            if not current_device or current_device.fingerprint != data['fingerprint']:
                raise ValueError("Invalid device")
        except Exception:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_device, *args, **kwargs)
    return decorated