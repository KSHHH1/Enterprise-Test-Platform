from flask import Blueprint, request, jsonify, render_template
from .services import register_new_device, authenticate_device, create_token, token_required
from models.user import User
from werkzeug.security import check_password_hash
import jwt
from datetime import datetime, timedelta
import os

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    """
    注册新设备。
    """
    data = request.get_json()
    if not data or 'fingerprint' not in data:
        return jsonify({'message': 'Fingerprint is required'}), 400
    
    try:
        password = register_new_device(data)
        return jsonify({'message': 'Device registered successfully', 'password': password}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    """
    用户登录。
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400

    username = data['username']
    password = data['password']
    
    # 查找用户
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        # 生成JWT token
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, os.environ.get('SECRET_KEY', 'dev-secret-key'), algorithm='HS256')
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

@bp.route('/device-login', methods=['POST'])
def device_login():
    """
    设备登录。
    """
    data = request.get_json()
    if not data or 'fingerprint' not in data or 'password' not in data:
        return jsonify({'message': 'Fingerprint and password are required'}), 400

    token, device = authenticate_device(data)
    
    if token:
        return jsonify(access_token=token, device_name=device.name)
    
    return jsonify({'message': 'Invalid credentials'}), 401

@bp.route('/verify', methods=['GET'])
def verify():
    """
    验证JWT token。
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'message': 'Token缺失'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, os.environ.get('SECRET_KEY', 'dev-secret-key'), algorithms=['HS256'])
        user = User.query.get(payload['user_id'])
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        else:
            return jsonify({'success': False, 'message': '用户不存在'}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token已过期'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Token无效'}), 401

@bp.route('/status')
@token_required
def status(current_device):
    """
    检查当前JWT Token的有效性.
    如果token有效, 返回设备信息.
    `token_required` 装饰器会处理无效或缺失的token.
    """
    return jsonify({
        'status': 'ok',
        'device_name': current_device.name,
        'device_id': current_device.id
    })