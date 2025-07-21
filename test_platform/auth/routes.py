from flask import Blueprint, request, jsonify
from .services import register_new_device, authenticate_device, create_token, token_required

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
    设备登录。
    """
    data = request.get_json()
    if not data or 'fingerprint' not in data or 'password' not in data:
        return jsonify({'message': 'Fingerprint and password are required'}), 400

    token, device = authenticate_device(data)
    
    if token:
        return jsonify(access_token=token, device_name=device.name)
    
    return jsonify({'message': 'Invalid credentials'}), 401

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