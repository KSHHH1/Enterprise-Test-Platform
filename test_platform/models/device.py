# models/device.py
from test_platform.app import db

class Device(db.Model):
    """
    设备模型，用于设备指纹认证
    """
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    fingerprint = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    registered_ip = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_login_at = db.Column(db.DateTime, onupdate=db.func.now())
    password_hash = db.Column(db.String(128), nullable=False) 