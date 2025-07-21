"""
企业测试平台 - Agent API模块
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from typing import Dict, Any

from ...config import get_config
from ...utils import get_logger
from .agent_core import AgentCore

class AgentAPI:
    """Agent API类"""
    
    def __init__(self, config_name: str = None):
        self.config = get_config(config_name)
        self.logger = get_logger('enterprise_platform.agent_api')
        self.agent_core = AgentCore(config_name)
        
        # 创建Flask应用
        self.app = Flask(__name__)
        CORS(self.app)
        
        # 注册路由
        self._register_routes()
        
        self.logger.info("Agent API初始化完成")
    
    def _register_routes(self):
        """注册API路由"""
        
        @self.app.route('/api/serials', methods=['GET'])
        def get_serials():
            """获取串口列表"""
            try:
                ports = self.agent_core.get_serial_ports()
                return jsonify([port.to_dict() for port in ports])
            except Exception as e:
                self.logger.error(f"获取串口列表API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/cases', methods=['GET'])
        def get_cases():
            """获取测试用例列表"""
            try:
                cases = self.agent_core.get_test_cases()
                return jsonify([case.to_dict() for case in cases])
            except Exception as e:
                self.logger.error(f"获取测试用例列表API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/hosts', methods=['GET'])
        def get_hosts():
            """获取手动配置的主机列表"""
            try:
                hosts = self.agent_core.get_manual_hosts()
                return jsonify(hosts)
            except Exception as e:
                self.logger.error(f"获取主机列表API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/test/run', methods=['POST'])
        def run_test():
            """运行测试用例"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "请求数据为空"}), 400
                
                case_name = data.get('case_name')
                serial_port = data.get('serial_port')
                
                if not case_name or not serial_port:
                    return jsonify({"error": "缺少必要参数: case_name, serial_port"}), 400
                
                result = self.agent_core.run_test_case(case_name, serial_port)
                
                if result.success:
                    return jsonify(result.to_dict())
                else:
                    return jsonify(result.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"运行测试API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/test/<test_id>', methods=['GET'])
        def get_test_result(test_id):
            """获取测试结果"""
            try:
                result = self.agent_core.get_test_result(test_id)
                if result:
                    return jsonify(result.to_dict())
                else:
                    return jsonify({"error": "测试不存在"}), 404
            except Exception as e:
                self.logger.error(f"获取测试结果API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/tests', methods=['GET'])
        def get_running_tests():
            """获取所有运行中的测试"""
            try:
                tests = self.agent_core.get_running_tests()
                return jsonify([test.to_dict() for test in tests])
            except Exception as e:
                self.logger.error(f"获取运行中测试API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/test/<test_id>/cancel', methods=['POST'])
        def cancel_test(test_id):
            """取消测试"""
            try:
                result = self.agent_core.cancel_test(test_id)
                
                if result.success:
                    return jsonify(result.to_dict())
                else:
                    return jsonify(result.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"取消测试API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """健康检查"""
            return jsonify({
                "status": "healthy",
                "service": "agent",
                "version": "1.0.0"
            })
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({"error": "API端点不存在"}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({"error": "内部服务器错误"}), 500
    
    def run(self, host: str = None, port: int = None, debug: bool = None):
        """运行Agent API服务"""
        host = host or self.config.AGENT_HOST
        port = port or self.config.AGENT_PORT
        debug = debug if debug is not None else self.config.DEBUG
        
        self.logger.info(f"启动Agent API服务: {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)