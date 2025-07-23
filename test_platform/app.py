import os
from flask import Flask, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from database import db

# 初始化扩展
socketio = SocketIO()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name=None):
    """应用工厂函数"""
    print('Creating Flask app...')
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG') or 'default'
    
    from config import config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    jwt.init_app(app)
    CORS(app)

    # 导入模型 - 确保所有模型都被导入
    from models.device import Device
    from models.user import User
    from models.test_case import TestCase, TestSuite
    from models.firmware import Firmware, FirmwareDeployment
    from models.test_result import TestResult, TestExecution
    from models.alert import Alert, AlertRule

    # 注册蓝图
    from core import bp as core_bp
    from auth import bp as auth_bp
    from dashboard import bp as dashboard_bp
    
    # 注册API蓝图
    from api.auth import bp as api_auth_bp
    from api.user_auth import bp as api_user_auth_bp
    from api.test_cases import bp as test_cases_bp
    from api.test_results import bp as test_results_bp
    from api.firmware import bp as firmware_bp
    from api.hardware import bp as hardware_bp
    from api.test_execution import bp as test_execution_bp
    from api.devices import bp as devices_bp
    from api.system import bp as system_bp
    from api.dashboard import bp as api_dashboard_bp
    from api.alerts import bp as alerts_bp
    from api.reports import bp as reports_bp
    
    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    # 注册API路由
    app.register_blueprint(api_auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_user_auth_bp, url_prefix='/api/user-auth')
    app.register_blueprint(test_cases_bp, url_prefix='/api/test-cases')
    app.register_blueprint(test_results_bp, url_prefix='/api/test-results')
    app.register_blueprint(firmware_bp, url_prefix='/api/firmware')
    app.register_blueprint(hardware_bp, url_prefix='/api/hardware')
    app.register_blueprint(test_execution_bp, url_prefix='/api/test-execution')
    app.register_blueprint(devices_bp, url_prefix='/api/devices')
    app.register_blueprint(system_bp, url_prefix='/api/system')
    app.register_blueprint(api_dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')

    # 页面路由 - 重定向到React前端
    @app.route('/')
    def index():
        """主页重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000')
    
    @app.route('/login')
    def login_page():
        """登录页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/login')
    
    @app.route('/auth/login')
    def auth_login_page():
        """认证登录页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/login')
    
    @app.route('/dashboard')
    def dashboard_page():
        """仪表板页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/dashboard')
    
    @app.route('/devices')
    def devices_page():
        """设备管理页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/test-management')
    
    @app.route('/devices/add')
    def devices_add_page():
        """添加设备页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/test-management')
    
    @app.route('/test-cases')
    def test_cases_page():
        """测试用例管理页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/test-management')
    
    @app.route('/test-cases/create')
    def test_cases_create_page():
        """创建测试用例页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/test-management')
    
    @app.route('/test-results')
    def test_results_page():
        """测试结果页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/test-results')
    
    @app.route('/reports')
    def reports_page():
        """报告页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/test-results')
    
    @app.route('/system/health')
    def system_health_page():
        """系统监控页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/hardware-status')
    
    @app.route('/system/settings')
    def system_settings_page():
        """系统设置页面重定向到React前端"""
        from flask import redirect
        return redirect('http://localhost:3000/system-settings')

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
            db.session.execute(db.text('SELECT 1'))
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # 检查Redis连接（如果配置了）
        redis_url = app.config.get('REDIS_URL')
        if redis_url and not redis_url.startswith('redis://localhost'):
            try:
                import redis
                r = redis.from_url(redis_url)
                r.ping()
                health_status["services"]["redis"] = "healthy"
            except Exception as e:
                health_status["services"]["redis"] = f"unhealthy: {str(e)}"
                # Redis失败不影响整体健康状态，因为它是可选的
        else:
            health_status["services"]["redis"] = "not configured"
        
        # 返回适当的HTTP状态码
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code

    return app

if __name__ == '__main__':
    app = create_app()
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # 创建默认管理员用户
        from models.user import User
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print('Created default admin user: admin/admin123')
    
    # 初始化告警服务
    from services.alert_service import alert_service
    alert_service.set_app(app)
    alert_service.set_socketio(socketio)
    alert_service.start_monitoring()
    
    # 启动应用
    socketio.run(app, host='0.0.0.0', port=5002, debug=True)