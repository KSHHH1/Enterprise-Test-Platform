import os
from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 初始化扩展
db = SQLAlchemy()
socketio = SocketIO()
migrate = Migrate()

def create_app(debug=False):
    print('Creating Flask app...')
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    # 导入模型以便迁移检测
    from .models.device import Device

    # 从环境变量加载配置
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # 绑定扩展到应用实例
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, message_queue=os.environ.get('REDIS_URL'))

    # 注册蓝图
    from .core import bp as core_bp
    app.register_blueprint(core_bp)

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    # 健康检查路由
    @app.route('/ping')
    def ping():
        return jsonify(message="pong")
    
    @app.route('/health')
    def health():
        """完整的健康检查端点"""
        import time
        from datetime import datetime
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {}
        }
        
        # 检查数据库连接
        try:
            db.session.execute('SELECT 1')
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # 检查Redis连接（如果配置了）
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            try:
                import redis
                r = redis.from_url(redis_url)
                r.ping()
                health_status["services"]["redis"] = "healthy"
            except Exception as e:
                health_status["services"]["redis"] = f"unhealthy: {str(e)}"
                health_status["status"] = "unhealthy"
        
        # 返回适当的HTTP状态码
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code

    return app