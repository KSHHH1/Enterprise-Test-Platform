# models/device.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class Device(db.Model):
    """
    设备模型，用于设备管理和认证
    """
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    
    # 设备基本信息
    name = db.Column(db.String(100), nullable=False, unique=True)
    device_type = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(100))
    serial_number = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance
    
    # 网络配置
    ip_address = db.Column(db.String(45), unique=True)
    serial_port = db.Column(db.String(20))
    
    # 版本信息
    firmware_version = db.Column(db.String(50))
    hardware_version = db.Column(db.String(50))
    
    # 配置信息
    network_config = db.Column(db.JSON)
    test_config = db.Column(db.JSON)
    
    # 认证相关（保留原有功能）
    fingerprint = db.Column(db.String(255), unique=True, nullable=True, index=True)
    registered_ip = db.Column(db.String(45))
    last_login_ip = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    password_hash = db.Column(db.String(128))
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # 创建者
    created_by = db.Column(db.String(50))
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """检查密码"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'device_type': self.device_type,
            'model': self.model,
            'serial_number': self.serial_number,
            'description': self.description,
            'location': self.location,
            'status': self.status,
            'ip_address': self.ip_address,
            'serial_port': self.serial_port,
            'firmware_version': self.firmware_version,
            'hardware_version': self.hardware_version,
            'network_config': self.network_config,
            'test_config': self.test_config,
            'fingerprint': self.fingerprint,
            'registered_ip': self.registered_ip,
            'last_login_ip': self.last_login_ip,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_by': self.created_by
        }