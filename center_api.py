#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Center API - 企业测试平台中心服务
提供主机管理、Agent发现和测试协调功能
"""
from flask import Flask, request, jsonify, render_template_string, send_from_directory, session
from flask_cors import CORS
import json
import os
import socket
import threading
import time
import requests
import ipaddress
import subprocess
import logging
import uuid
from enterprise_platform.core.machine_manager import get_machine_manager

app = Flask(__name__, static_folder='test_platform/static', static_url_path='/static')
# 启用CORS支持跨域访问，包括VPN网段
CORS(app, origins=['*'], allow_headers=['*'], methods=['*'])

# 配置session
# 使用环境变量或随机生成的密钥以提高安全性
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
manual_hosts_file = "manual_hosts.json"
discovered_hosts = {}
host_status = {}

# 初始化测试机管理器
machine_manager = get_machine_manager()

def load_manual_hosts():
    """加载手动配置的主机"""
    try:
        if os.path.exists(manual_hosts_file):
            with open(manual_hosts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载手动主机配置失败: {e}")
    return []

def save_manual_hosts(hosts):
    """保存手动配置的主机"""
    try:
        with open(manual_hosts_file, 'w', encoding='utf-8') as f:
            json.dump(hosts, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存手动主机配置失败: {e}")
        return False

def get_local_networks():
    """获取本地网络段"""
    networks = []
    try:
        # 获取本机IP地址
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # 生成常见的网络段
        ip_parts = local_ip.split('.')
        base_network = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        networks.append(base_network)
        
        # 添加其他常见网络段
        common_networks = [
            "192.168.1.0/24",
            "192.168.0.0/24", 
            "10.0.0.0/24",
            "172.16.0.0/24"
        ]
        
        for network in common_networks:
            if network not in networks:
                networks.append(network)
                
    except Exception as e:
        logger.error(f"获取本地网络段失败: {e}")
        # 默认网络段
        networks = ["192.168.1.0/24", "192.168.0.0/24"]
    
    return networks

def check_agent_online(ip, port=5001, timeout=3):
    """检查Agent是否在线"""
    try:
        response = requests.get(f"http://{ip}:{port}/", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def get_agent_info(ip, port=5001, timeout=3):
    """获取Agent信息"""
    try:
        response = requests.get(f"http://{ip}:{port}/", timeout=timeout)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def discover_hosts_in_network(network):
    """在指定网络段发现主机"""
    discovered = []
    try:
        net = ipaddress.IPv4Network(network, strict=False)
        for ip in net.hosts():
            ip_str = str(ip)
            if check_agent_online(ip_str):
                info = get_agent_info(ip_str)
                host_info = {
                    "name": f"Agent-{ip_str}",
                    "ip": ip_str,
                    "port": 5001,
                    "status": "在线",
                    "type": "自动发现",
                    "info": info
                }
                discovered.append(host_info)
                logger.info(f"发现Agent: {ip_str}")
    except Exception as e:
        logger.error(f"网络发现失败 {network}: {e}")
    
    return discovered

@app.route('/')
def index():
    """主页 - 返回Web界面"""
    try:
        return send_from_directory('.', 'web_interface.html')
    except Exception as e:
        logger.error(f"返回主页失败: {e}")
        return jsonify({
            "service": "Enterprise Test Platform Center",
            "version": "1.0.0",
            "status": "running",
            "error": "Web界面文件未找到"
        })

@app.route('/web_interface.html')
def web_interface():
    """Web界面"""
    try:
        return send_from_directory('.', 'web_interface.html')
    except Exception as e:
        logger.error(f"返回Web界面失败: {e}")
        return "Web界面文件未找到", 404

@app.route('/login.html')
def login_page():
    """登录页面"""
    try:
        return send_from_directory('.', 'login.html')
    except Exception as e:
        logger.error(f"返回登录页面失败: {e}")
        return "登录页面文件未找到", 404

@app.route('/test-static')
def test_static():
    """测试静态文件路由"""
    return f"Static route working! Looking for files in: {os.path.abspath('test_platform/static')}"

@app.route('/api/hosts')
def get_hosts():
    """获取所有主机列表"""
    manual_hosts = load_manual_hosts()
    all_hosts = []
    
    # 添加手动配置的主机
    for host in manual_hosts:
        host_ip = host.get('ip')
        # 检查在线状态
        online = check_agent_online(host_ip)
        
        # 获取测试机状态
        machine_status_info = machine_manager.get_machine_status(host_ip)
        
        host_info = {
            "name": host.get('name', f"Host-{host_ip}"),
            "ip": host_ip,
            "port": host.get('port', 5001),
            "location": host.get('location', ''),
            "status": "在线" if online else "离线",
            "type": "手动添加",
            "machine_status": machine_status_info['status'],
            "is_busy": not machine_status_info['available'],
            "session_info": machine_status_info.get('session')
        }
        all_hosts.append(host_info)
        host_status[host_ip] = online
    
    # 添加自动发现的主机
    for ip, host in discovered_hosts.items():
        if not any(h.get('ip') == ip for h in manual_hosts):
            # 获取测试机状态
            machine_status_info = machine_manager.get_machine_status(ip)
            
            host_info = {
                "name": host.get('name', f"Agent-{ip}"),
                "ip": ip,
                "port": host.get('port', 5001),
                "location": host.get('location', ''),
                "status": host.get('status', '未知'),
                "type": "自动发现",
                "machine_status": machine_status_info['status'],
                "is_busy": not machine_status_info['available'],
                "session_info": machine_status_info.get('session')
            }
            all_hosts.append(host_info)
    
    return jsonify(all_hosts)

@app.route('/api/hosts', methods=['POST'])
def add_host():
    """添加手动主机"""
    data = request.get_json()
    
    if not data or 'ip' not in data:
        return jsonify({"error": "缺少IP地址"}), 400
    
    manual_hosts = load_manual_hosts()
    
    # 检查是否已存在
    if any(h.get('ip') == data['ip'] for h in manual_hosts):
        return jsonify({"error": "主机已存在"}), 400
    
    # 创建主机信息
    host_info = {
        "name": data.get('name', f"Host-{data['ip']}"),
        "ip": data['ip'],
        "port": data.get('port', 5001),
        "location": data.get('location', ''),
        "status": '未知',
        "type": "手动添加"
    }
    
    manual_hosts.append(host_info)
    
    if save_manual_hosts(manual_hosts):
        return jsonify(host_info)
    else:
        return jsonify({"error": "保存失败"}), 500

@app.route('/api/hosts/<host_ip>', methods=['DELETE'])
def delete_host(host_ip):
    """删除手动主机"""
    manual_hosts = load_manual_hosts()
    
    # 查找并删除主机
    manual_hosts = [h for h in manual_hosts if h.get('ip') != host_ip]
    
    if save_manual_hosts(manual_hosts):
        return jsonify({"message": "删除成功"})
    else:
        return jsonify({"error": "删除失败"}), 500

@app.route('/api/discover')
def discover_hosts():
    """自动发现主机"""
    networks = get_local_networks()
    all_discovered = []
    
    for network in networks:
        logger.info(f"扫描网络段: {network}")
        discovered = discover_hosts_in_network(network)
        all_discovered.extend(discovered)
        
        # 更新全局发现列表
        for host in discovered:
            discovered_hosts[host['ip']] = host
    
    return jsonify({
        "message": f"发现完成，共找到 {len(all_discovered)} 个Agent",
        "discovered": all_discovered,
        "networks_scanned": networks
    })

@app.route('/api/hosts/<host_ip>/test')
def test_host_connection(host_ip):
    """测试主机连接"""
    online = check_agent_online(host_ip)
    info = get_agent_info(host_ip) if online else None
    
    return jsonify({
        "ip": host_ip,
        "online": online,
        "status": "在线" if online else "离线",
        "info": info
    })

@app.route('/api/hosts/<host_ip>/serials')
def get_host_serials(host_ip):
    """获取主机串口列表"""
    try:
        response = requests.get(f"http://{host_ip}:5001/serials", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "获取串口列表失败"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hosts/<host_ip>/cases')
def get_host_cases(host_ip):
    """获取主机测试用例列表"""
    try:
        response = requests.get(f"http://{host_ip}:5001/cases", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "获取测试用例失败"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hosts/<host_ip>/run_case', methods=['POST'])
def run_host_case(host_ip):
    """在指定主机运行测试用例"""
    try:
        # 强制用户登录
        if 'user_id' not in session or 'user_name' not in session:
            return jsonify({"success": False, "error": "用户未登录或会话无效，请重新登录", "redirect_to_login": True}), 401
        user_id = session['user_id']
        user_name = session['user_name']

        # 获取请求数据
        data = request.get_json() or {}
        test_case = data.get('test_case', '未知测试用例')
        serial_port = data.get('serial_port', 'auto')
        
        # 尝试获取测试机
        success, message = machine_manager.acquire_machine(host_ip, user_id, user_name, test_case, serial_port, manual=False)
        if not success:
            return jsonify({"error": f"无法获取测试机: {message}"}), 409
        
        # 转换为测试机agent期望的格式
        agent_data = {
            "case": test_case,
            "serial": serial_port
        }
        
        response = requests.post(f"http://{host_ip}:5001/run_case", 
                               json=agent_data, timeout=30)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            # 如果测试运行失败，释放测试机
            machine_manager.release_machine(host_ip, user_id)
            return jsonify({"error": f"运行测试用例失败，状态码: {response.status_code}"}), 500
    except requests.exceptions.ConnectionError as e:
        # 如果出现异常，释放测试机
        if 'user_id' in session:
            machine_manager.release_machine(host_ip, session['user_id'])
        return jsonify({"error": f"无法连接到测试机 {host_ip}:5001，请确保测试机agent正在运行"}), 500
    except Exception as e:
        # 如果出现异常，释放测试机
        if 'user_id' in session:
            machine_manager.release_machine(host_ip, session['user_id'])
        return jsonify({"error": str(e)}), 500

@app.route('/api/hosts/<host_ip>/acquire', methods=['POST'])
def acquire_machine(host_ip):
    """获取测试机使用权"""
    try:
        # 强制用户登录
        if 'user_id' not in session or 'user_name' not in session:
            return jsonify({"success": False, "error": "用户未登录或会话无效，请重新登录", "redirect_to_login": True}), 401
        user_id = session['user_id']
        user_name = session['user_name']

        # 获取请求数据
        data = request.get_json() or {}
        test_case = data.get('test_case', '手动获取')
        serial_port = data.get('serial_port', '')
        
        success, message = machine_manager.acquire_machine(host_ip, user_id, user_name, test_case, serial_port, manual=False)
        
        if success:
            return jsonify({"success": True, "message": message, "user_id": user_id})
        else:
            return jsonify({"success": False, "error": message}), 409
    except Exception as e:
        logger.error(f"获取测试机使用权失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/hosts/<host_ip>/release', methods=['POST'])
def release_machine(host_ip):
    """释放测试机使用权"""
    try:
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "无效的会话"}), 400
        
        user_id = session['user_id']
        success, message = machine_manager.release_machine(host_ip, user_id)
        
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/hosts/<host_ip>/heartbeat', methods=['POST'])
def update_heartbeat(host_ip):
    """更新测试机心跳"""
    try:
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "无效的会话"}), 400
        
        user_id = session['user_id']
        success, message = machine_manager.update_heartbeat(host_ip, user_id)
        
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/hosts/<host_ip>/force_release', methods=['POST'])
def force_release_machine(host_ip):
    """强制释放测试机（管理员功能）"""
    try:
        # 获取管理员用户信息
        data = request.get_json() or {}
        admin_user = data.get('admin_user', 'Admin')
        
        success, message = machine_manager.force_release_machine(host_ip, admin_user)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/vpn_test')
def vpn_test():
    """VPN访问测试页面"""
    try:
        with open('vpn_test.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"<h1>错误</h1><p>无法加载测试页面: {str(e)}</p>", 500

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录验证"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        device_fingerprint = data.get('device_fingerprint', '')
        
        # 简单密码验证
        if password != '123456':
            return jsonify({"success": False, "error": "密码错误"}), 401
        
        # 获取客户端IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        # 生成用户ID（基于设备指纹和IP）
        import hashlib
        user_id = hashlib.md5(f"{device_fingerprint}_{client_ip}".encode()).hexdigest()[:12]
        user_name = f"User-{user_id}"
        
        # 保存到会话
        session['user_id'] = user_id
        session['user_name'] = user_name
        session['client_ip'] = client_ip
        session['device_fingerprint'] = device_fingerprint
        session['login_time'] = time.time()
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "user_name": user_name,
            "client_ip": client_ip,
            "message": "登录成功"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出"""
    try:
        # 释放用户占用的所有测试机
        if 'user_id' in session:
            user_id = session['user_id']
            # 获取用户占用的所有测试机并释放
            user_sessions = machine_manager.get_user_sessions(user_id)
            for host_ip in user_sessions:
                machine_manager.release_machine(host_ip, user_id)
        
        # 清除会话
        session.clear()
        
        return jsonify({"success": True, "message": "登出成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/machine_status')
def get_machine_status():
    """获取所有测试机的状态"""
    try:
        status = machine_manager.get_all_machine_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user_info')
def get_user_info():
    """获取当前用户信息"""
    try:
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "未登录"}), 401
        
        user_id = session['user_id']
        user_name = session.get('user_name', f'User-{user_id}')
        client_ip = session.get('client_ip', 'unknown')
        login_time = session.get('login_time', 0)
        
        # 获取用户占用的测试机
        user_sessions = machine_manager.get_user_sessions(user_id)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "user_name": user_name,
            "client_ip": client_ip,
            "login_time": login_time,
            "occupied_machines": list(user_sessions)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/network_info')
def network_info():
    """获取网络信息用于诊断"""
    try:
        import subprocess
        import socket
        
        # 获取客户端IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        # 获取服务器所有IP地址
        hostname = socket.gethostname()
        server_ips = []
        
        try:
            # 获取主机名对应的IP
            main_ip = socket.gethostbyname(hostname)
            server_ips.append(main_ip)
        except:
            pass
        
        try:
            # 获取所有IP地址
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if ip not in server_ips and ip != '127.0.0.1':
                    server_ips.append(ip)
        except:
            pass
        
        # 获取网络接口信息
        try:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
            ipconfig_output = result.stdout
        except:
            ipconfig_output = "无法获取网络接口信息"
        
        return jsonify({
            "client_ip": client_ip,
            "server_ips": server_ips,
            "server_hostname": hostname,
            "service_port": 5002,
            "access_urls": [f"http://{ip}:5002" for ip in server_ips],
            "ipconfig_info": ipconfig_output,
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/host/<host_ip>/test_status/<test_id>')
def proxy_test_status(host_ip, test_id):
    """代理测试状态查询"""
    try:
        response = requests.get(f"http://{host_ip}:5001/test_status/{test_id}", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"success": False, "error": "获取测试状态失败"}), response.status_code
    except Exception as e:
        return jsonify({"success": False, "error": f"连接测试机失败: {str(e)}"}), 500

@app.route('/api/host/<host_ip>/stop_test/<test_id>', methods=['POST'])
def proxy_stop_test(host_ip, test_id):
    """代理停止测试请求"""
    try:
        # 检查用户身份
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "用户未登录"}), 401
        
        user_id = session['user_id']
        
        # 检查用户是否有权限操作这台测试机
        machine_status = machine_manager.get_machine_status(host_ip)
        if machine_status['status'] == 'busy' and machine_status.get('session', {}).get('user_id') != user_id:
            return jsonify({"success": False, "error": "无权限操作此测试机"}), 403
        
        # 获取请求数据
        data = request.get_json() or {}
        user_name = data.get('user_name', session.get('user_name', f'User-{user_id[:8]}'))
        
        # 发送停止测试请求到Agent
        response = requests.post(f"http://{host_ip}:5001/stop_test/{test_id}", 
                               json={"user_name": user_name}, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            # 停止测试成功，但不自动释放测试机（需要手动操作）
            if result.get('success', False):
                logger.info(f"用户 {user_name} 停止测试 {host_ip}")
            
            return jsonify(result)
        else:
            return jsonify({"success": False, "error": "停止测试失败"}), response.status_code
    except Exception as e:
        logger.error(f"停止测试失败: {str(e)}")
        return jsonify({"success": False, "error": f"连接测试机失败: {str(e)}"}), 500

@app.route('/api/host/<host_ip>/manual_occupy', methods=['POST'])
def manual_occupy_machine(host_ip):
    """手动占用测试机"""
    try:
        # 检查用户身份
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "用户未登录"}), 401
        
        user_id = session['user_id']
        user_name = session.get('user_name', f'User-{user_id[:8]}')
        
        # 检查测试机是否在线
        if not check_agent_online(host_ip):
            return jsonify({"success": False, "error": "测试机离线"}), 400
        
        # 尝试手动占用测试机
        success, message = machine_manager.acquire_machine(host_ip, user_id, user_name, "手动占用", "", manual=True)
        
        if success:
            logger.info(f"用户 {user_name} 手动占用测试机 {host_ip}")
            return jsonify({"success": True, "message": "手动占用成功"})
        else:
            return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        logger.error(f"手动占用测试机失败: {str(e)}")
        return jsonify({"success": False, "error": f"手动占用失败: {str(e)}"}), 500

@app.route('/api/host/<host_ip>/manual_release', methods=['POST'])
def manual_release_machine(host_ip):
    """手动释放测试机"""
    try:
        # 检查用户身份
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "用户未登录"}), 401
        
        user_id = session['user_id']
        user_name = session.get('user_name', f'User-{user_id[:8]}')
        
        # 检查用户是否有权限释放这台测试机
        machine_status = machine_manager.get_machine_status(host_ip)
        if machine_status['status'] == 'busy':
            session_info = machine_status.get('session', {})
            if session_info.get('user_id') != user_id:
                return jsonify({"success": False, "error": "无权限释放此测试机"}), 403
        
        # 尝试手动释放测试机
        success, message = machine_manager.release_machine(host_ip, user_id)
        
        if success:
            logger.info(f"用户 {user_name} 手动释放测试机 {host_ip}")
            return jsonify({"success": True, "message": "手动释放成功"})
        else:
            return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        logger.error(f"手动释放测试机失败: {str(e)}")
        return jsonify({"success": False, "error": f"手动释放失败: {str(e)}"}), 500

@app.route('/api/hosts/<host_ip>/switch', methods=['POST'])
def handle_switch_command(host_ip):
    """处理开关命令"""
    try:
        # 检查用户身份
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "用户未登录"}), 401
        
        user_id = session['user_id']
        user_name = session.get('user_name', f'User-{user_id[:8]}')
        
        # 获取请求数据
        data = request.get_json() or {}
        switch_type = data.get('switch_type', '')
        state = data.get('state', False)
        
        # 检查测试机是否在线
        if not check_agent_online(host_ip):
            return jsonify({"success": False, "error": "测试机离线"}), 400
        
        # 处理占用控制开关
        if switch_type == 'occupy':
            if state:
                # 占用测试机
                success, message = machine_manager.acquire_machine(host_ip, user_id, user_name, "开关占用", "", manual=True)
            else:
                # 释放测试机
                success, message = machine_manager.release_machine(host_ip, user_id)
            
            if success:
                action = "占用" if state else "释放"
                logger.info(f"用户 {user_name} {action}测试机 {host_ip}")
                return jsonify({"success": True, "message": f"{action}成功"})
            else:
                return jsonify({"success": False, "error": message}), 400
        else:
            return jsonify({"success": False, "error": f"不支持的开关类型: {switch_type}"}), 400
            
    except Exception as e:
        logger.error(f"处理开关命令失败: {str(e)}")
        return jsonify({"success": False, "error": f"处理开关命令失败: {str(e)}"}), 500

@app.route('/api/hosts/<host_ip>/switch_status', methods=['GET'])
def get_switch_status(host_ip):
    """获取开关状态"""
    try:
        # 获取测试机状态
        machine_status = machine_manager.get_machine_status(host_ip)
        
        # 返回开关状态
        switch_states = {
            "occupy": machine_status['status'] == 'busy'
        }
        
        return jsonify({
            "success": True,
            "data": switch_states
        })
        
    except Exception as e:
        logger.error(f"获取开关状态失败: {str(e)}")
        return jsonify({"success": False, "error": f"获取开关状态失败: {str(e)}"}), 500

if __name__ == '__main__':
    print("启动企业测试平台中心服务...")
    print("服务地址: http://localhost:5002")
    print("网络访问地址: http://192.168.0.122:5002")
    print("网络访问地址: http://10.8.0.30:5002")
    app.run(host='0.0.0.0', port=5002, debug=True)