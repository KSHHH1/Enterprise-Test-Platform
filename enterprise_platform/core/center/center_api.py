"""
企业测试平台 - Center API模块
"""
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from typing import Dict, Any

from ...config import get_config
from ...utils import get_logger
from .center_core import CenterCore

class CenterAPI:
    """Center API类"""
    
    def __init__(self, config_name: str = None):
        self.config = get_config(config_name)
        self.logger = get_logger('enterprise_platform.center_api')
        self.center_core = CenterCore(config_name)
        
        # 创建Flask应用
        self.app = Flask(__name__)
        CORS(self.app)
        
        # 注册路由
        self._register_routes()
        
        self.logger.info("Center API初始化完成")
    
    def _register_routes(self):
        """注册API路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template_string(self._get_index_template())
        
        @self.app.route('/api/hosts', methods=['GET'])
        def get_hosts():
            """获取所有主机"""
            try:
                hosts = self.center_core.get_hosts()
                return jsonify([host.to_dict() for host in hosts])
            except Exception as e:
                self.logger.error(f"获取主机列表API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/agents', methods=['GET'])
        def get_agents():
            """获取所有Agent（与hosts接口兼容）"""
            try:
                hosts = self.center_core.get_hosts()
                return jsonify([host.to_dict() for host in hosts])
            except Exception as e:
                self.logger.error(f"获取Agent列表API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/host/<host_ip>', methods=['GET'])
        def get_host(host_ip):
            """获取指定主机信息"""
            try:
                host = self.center_core.get_host(host_ip)
                if host:
                    return jsonify(host.to_dict())
                else:
                    return jsonify({"error": "主机不存在"}), 404
            except Exception as e:
                self.logger.error(f"获取主机信息API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/host/<host_ip>/serials', methods=['GET'])
        def get_host_serials(host_ip):
            """获取主机串口列表"""
            try:
                serials = self.center_core.get_host_serials(host_ip)
                # 返回简单的字符串数组，前端期望这种格式
                return jsonify([serial.device for serial in serials])
            except Exception as e:
                self.logger.error(f"获取主机串口列表API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/host/<host_ip>/cases', methods=['GET'])
        def get_host_cases(host_ip):
            """获取主机测试用例列表"""
            try:
                cases = self.center_core.get_host_cases(host_ip)
                # 返回简单的字符串数组，前端期望这种格式
                return jsonify([case.name for case in cases])
            except Exception as e:
                self.logger.error(f"获取主机测试用例列表API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/hosts', methods=['POST'])
        def add_host():
            """添加主机"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "请求数据为空"}), 400
                
                ip = data.get('ip')
                name = data.get('name', ip)
                
                if not ip:
                    return jsonify({"error": "缺少必要参数: ip"}), 400
                
                # 验证IP格式
                import re
                ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
                if not re.match(ip_pattern, ip):
                    return jsonify({"error": "IP地址格式不正确"}), 400
                
                result = self.center_core.add_host(ip, name)
                
                if result.success:
                    return jsonify(result.to_dict())
                else:
                    return jsonify(result.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"添加主机API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/host/<host_ip>', methods=['DELETE'])
        def delete_host(host_ip):
            """删除主机"""
            try:
                result = self.center_core.delete_host(host_ip)
                
                if result.success:
                    return jsonify(result.to_dict())
                else:
                    return jsonify(result.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"删除主机API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/host/<host_ip>', methods=['PUT'])
        def update_host(host_ip):
            """更新主机信息"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "请求数据为空"}), 400
                
                name = data.get('name')
                
                result = self.center_core.update_host(host_ip, name)
                
                if result.success:
                    return jsonify(result.to_dict())
                else:
                    return jsonify(result.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"更新主机API异常: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/host/<host_ip>/test/run', methods=['POST'])
        def run_test_on_host(host_ip):
            """在指定主机上运行测试"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "请求数据为空"}), 400
                
                case_name = data.get('case_name')
                serial_port = data.get('serial_port')
                
                if not case_name or not serial_port:
                    return jsonify({"error": "缺少必要参数: case_name, serial_port"}), 400
                
                result = self.center_core.run_test_on_host(host_ip, case_name, serial_port)
                
                if result.success:
                    return jsonify(result.to_dict())
                else:
                    return jsonify(result.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"运行测试API异常: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/host/<host_ip>/run_case', methods=['POST'])
        def run_case_on_host(host_ip):
            """在指定主机上运行测试用例（前端兼容接口）"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "请求数据为空"}), 400
                
                case_name = data.get('case')
                serial_port = data.get('serial')
                
                if not case_name or not serial_port:
                    return jsonify({"error": "缺少必要参数: case, serial"}), 400
                
                result = self.center_core.run_test_on_host(host_ip, case_name, serial_port)
                
                if result.success:
                    # 返回前端期望的格式
                    return jsonify({
                        "success": True,
                        "test_id": result.data.get('test_id') if result.data else None,
                        "status": result.data.get('status') if result.data else 'started',
                        "message": result.message
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": result.message
                    }), 400
                
            except Exception as e:
                self.logger.error(f"运行测试用例API异常: {e}")
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/host/<host_ip>/test/<test_id>', methods=['GET'])
        def get_test_result_from_host(host_ip, test_id):
            """从主机获取测试结果"""
            try:
                result = self.center_core.get_test_result_from_host(host_ip, test_id)
                if result:
                    return jsonify(result)
                else:
                    return jsonify({"error": "测试结果不存在"}), 404
            except Exception as e:
                self.logger.error(f"获取测试结果API异常: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/host/<host_ip>/test_status/<test_id>', methods=['GET'])
        def get_test_status_from_host(host_ip, test_id):
            """从主机获取测试状态（前端兼容接口）"""
            try:
                result = self.center_core.get_test_result_from_host(host_ip, test_id)
                if result:
                    # 返回前端期望的格式
                    return jsonify({
                        "success": True,
                        "data": result
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "测试结果不存在"
                    }), 404
            except Exception as e:
                self.logger.error(f"获取测试状态API异常: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @self.app.route('/api/host/<host_ip>/refresh', methods=['POST'])
        def refresh_host(host_ip):
            """刷新主机信息"""
            try:
                result = self.center_core.refresh_host(host_ip)
                
                if result.success:
                    return jsonify(result.to_dict())
                else:
                    return jsonify(result.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"刷新主机API异常: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """健康检查"""
            return jsonify({
                "status": "healthy",
                "service": "center",
                "version": "1.0.0"
            })
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({"error": "API端点不存在"}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({"error": "内部服务器错误"}), 500
    
    def _get_index_template(self) -> str:
        """获取主页模板"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>仪表盘 - 企业级测试平台</title>
    <style>
        body { display: flex; height: 100vh; margin: 0; font-family: Arial, sans-serif; }
        .sidebar { width: 280px; background: #f5f6fa; border-right: 1px solid #e0e0e0; padding: 24px 12px; box-sizing: border-box; }
        .sidebar h2 { font-size: 20px; margin-bottom: 16px; }
        .host-list { list-style: none; padding: 0; margin: 0; }
        .host-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 8px; margin-bottom: 8px; border-radius: 6px; background: #fff; cursor: pointer; border: 1px solid #e0e0e0; transition: background 0.2s; }
        .host-item.selected { background: #e6f7ff; border-color: #1890ff; }
        .host-item.busy { color: #aaa; background: #f0f0f0; cursor: not-allowed; }
        .host-info { flex: 1; }
        .host-name { font-weight: bold; }
        .host-meta { font-size: 12px; color: #888; }
        .host-actions { display: flex; gap: 4px; }
        .host-actions button { padding: 2px 6px; font-size: 11px; border: 1px solid #ddd; background: #fff; cursor: pointer; border-radius: 3px; }
        .host-actions button:hover { background: #f0f0f0; }
        .main { flex: 1; padding: 32px 40px; overflow-y: auto; }
        .section { margin-bottom: 32px; }
        .section h3 { margin-bottom: 12px; }
        .serial-list, .case-list { display: flex; flex-wrap: wrap; gap: 12px; }
        .serial-item, .case-item { background: #fafbfc; border: 1px solid #e0e0e0; border-radius: 5px; padding: 8px 16px; }
        .serial-item { display: flex; align-items: center; gap: 6px; }
        .case-item { display: flex; align-items: center; gap: 8px; }
        .case-item button { margin-left: 8px; }
        .actions { margin-top: 16px; }
        .log-area { width: 100%; height: 240px; background: #222; color: #0f0; font-family: monospace; font-size: 13px; border-radius: 4px; padding: 8px; margin-top: 8px; overflow-y: auto; }
        .download-btn { margin-top: 12px; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: #fefefe; margin: 15% auto; padding: 20px; border: 1px solid #888; width: 400px; border-radius: 8px; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: black; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .form-actions { display: flex; gap: 10px; justify-content: flex-end; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background-color: #1890ff; color: white; }
        .btn-secondary { background-color: #f0f0f0; color: #333; }
        .btn:hover { opacity: 0.8; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>可用电脑</h2>
        <div style="margin-bottom: 10px;">
            <button onclick="refreshHosts()" style="margin-right: 8px;">刷新列表</button>
            <label><input type="checkbox" id="autoRefresh"> 自动刷新</label>
        </div>
        <ul class="host-list" id="hostList"></ul>
        <button id="addHostBtn" onclick="showAddHostModal()">添加电脑</button>
    </div>
    <div class="main">
        <div id="hostDetail" style="display:none;">
            <div class="section">
                <h3>主机信息</h3>
                <div id="hostInfo"></div>
            </div>
            <div class="section">
                <h3>串口列表</h3>
                <div class="serial-list" id="serialList"></div>
            </div>
            <div class="section">
                <h3>测试用例</h3>
                <div class="case-list" id="caseList"></div>
                <div class="actions">
                    <button id="runAllBtn">全部测试</button>
                </div>
            </div>
            <div class="section">
                <h3>日志输出</h3>
                <div class="log-area" id="logArea">等待测试...</div>
                <button class="download-btn" id="downloadReportBtn">下载报告</button>
            </div>
        </div>
        <div id="emptyTip" style="color:#888; font-size:18px; text-align:center; margin-top:100px;">请选择左侧空闲电脑进行测试</div>
    </div>

    <!-- 添加/编辑主机模态框 -->
    <div id="hostModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modalTitle">添加电脑</h3>
                <span class="close" onclick="closeHostModal()">&times;</span>
            </div>
            <form id="hostForm">
                <div class="form-group">
                    <label for="hostIp">IP地址 *</label>
                    <input type="text" id="hostIp" name="ip" required placeholder="例如: 192.168.1.100">
                </div>
                <div class="form-group">
                    <label for="hostName">主机名称</label>
                    <input type="text" id="hostName" name="name" placeholder="例如: 测试机-01">
                </div>
                <div class="form-group">
                    <label for="hostLocation">位置</label>
                    <input type="text" id="hostLocation" name="location" placeholder="例如: 实验室A">
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="closeHostModal()">取消</button>
                    <button type="submit" class="btn btn-primary">保存</button>
                </div>
            </form>
        </div>
    </div>

    <script>
const API_BASE = '/api';
let hosts = [];
let selectedHostIdx = null;
let selectedSerial = null;
let serials = [];
let cases = [];
let editingHostIndex = null;

function fetchHosts() {
    const list = document.getElementById('hostList');
    list.innerHTML = '<div style="text-align:center;color:#888;">加载中...</div>';
    
    fetch(`${API_BASE}/hosts`)
        .then(res => {
            if (!res.ok) throw new Error('网络请求失败');
            return res.json();
        })
        .then(data => {
            hosts = data.map(host => ({
                ...host,
                status: host.status === 'online' ? '空闲' : '离线',
                location: host.location || '未知'
            }));
            renderHostList();
            renderHostDetail();
        })
        .catch(error => {
            list.innerHTML = `<div style="text-align:center;color:#ff4d4f;">加载失败: ${error.message}</div>`;
        });
}

function fetchSerialsAndCases(ip, cb) {
    Promise.all([
        fetch(`${API_BASE}/host/${ip}/serials`).then(res => res.json()),
        fetch(`${API_BASE}/host/${ip}/cases`).then(res => res.json())
    ]).then(([serialList, caseList]) => {
        serials = serialList.map(s => s.port || s.name || s);
        cases = caseList.map(c => c.name || c.display_name || c);
        cb && cb();
    }).catch(error => {
        console.error('获取串口和测试用例失败:', error);
        serials = [];
        cases = [];
        cb && cb();
    });
}

function renderHostList() {
    const list = document.getElementById('hostList');
    list.innerHTML = '';
    hosts.forEach((host, idx) => {
        const li = document.createElement('li');
        li.className = 'host-item' + (host.status === '忙碌' ? ' busy' : '') + (selectedHostIdx === idx ? ' selected' : '');
        li.innerHTML = `
            <div class="host-info">
                <div class="host-name">${host.name}</div>
                <div class="host-meta">${host.ip} | ${host.location} | ${host.status}</div>
            </div>
            <div class="host-actions">
                <button onclick="editHost(${idx})" title="编辑">编辑</button>
                <button onclick="deleteHost('${host.ip}')" title="删除">删除</button>
            </div>
        `;
        if (host.status === '空闲') {
            li.onclick = (e) => {
                if (e.target.tagName !== 'BUTTON') {
                    selectedHostIdx = idx;
                    fetchSerialsAndCases(host.ip, () => {
                        renderHostList();
                        renderHostDetail();
                    });
                }
            };
        }
        list.appendChild(li);
    });
}

function renderHostDetail() {
    const detail = document.getElementById('hostDetail');
    const tip = document.getElementById('emptyTip');
    if (selectedHostIdx === null) {
        detail.style.display = 'none';
        tip.style.display = '';
        return;
    }
    const host = hosts[selectedHostIdx];
    detail.style.display = '';
    tip.style.display = 'none';
    document.getElementById('hostInfo').innerHTML = `
        <b>名称：</b>${host.name} &nbsp; <b>IP：</b>${host.ip} &nbsp; <b>位置：</b>${host.location} &nbsp; <b>状态：</b>${host.status}
    `;
    // 串口
    const serialList = document.getElementById('serialList');
    serialList.innerHTML = '';
    if (serials.length === 0) {
        serialList.innerHTML = '<span style="color:#888">无可用串口</span>';
        selectedSerial = null;
    } else {
        selectedSerial = serials[0];
        serials.forEach((s) => {
            const div = document.createElement('div');
            div.className = 'serial-item';
            div.innerHTML = `<span>${s}</span>`;
            serialList.appendChild(div);
        });
    }
    // 用例
    const caseList = document.getElementById('caseList');
    caseList.innerHTML = '';
    if (cases.length === 0) {
        caseList.innerHTML = '<span style="color:#888">无测试用例</span>';
    } else {
        cases.forEach((c, i) => {
            const div = document.createElement('div');
            div.className = 'case-item';
            div.innerHTML = `<input type="checkbox" id="case${i}"><label for="case${i}">${c}</label><button>测试</button>`;
            div.querySelector('button').onclick = () => runCase(host.ip, selectedSerial, c);
            caseList.appendChild(div);
        });
    }
    document.getElementById('runAllBtn').onclick = () => runAllCases(host.ip, selectedSerial, cases);
    document.getElementById('downloadReportBtn').onclick = downloadReport;
    document.getElementById('logArea').textContent = '等待测试...';
}

function runCase(ip, serial, caseName) {
    const log = document.getElementById('logArea');
    if (!serial) { 
        log.innerHTML = '<span style="color:#ff4d4f;">请先选择串口</span>'; 
        return; 
    }
    log.innerHTML = `<span style="color:#1890ff;">正在请求远程执行：${caseName} @ ${serial}...</span>`;
    fetch(`${API_BASE}/host/${ip}/test/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_name: caseName, serial_port: serial })
    })
    .then(res => res.json())
    .then(data => {
        const logContent = data.data?.log || data.log || JSON.stringify(data);
        const formattedLog = formatLogOutput(logContent);
        log.innerHTML = formattedLog;
        log.scrollTop = log.scrollHeight;
    })
    .catch(error => {
        log.innerHTML = `<span style="color:#ff4d4f;">执行失败: ${error.message}</span>`;
    });
}

function formatLogOutput(logContent) {
    return logContent.replace(/\\n/g, '<br>').replace(/\\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');
}

function runAllCases(ip, serial, cases) {
    const log = document.getElementById('logArea');
    if (!serial) { 
        log.innerHTML = '<span style="color:#ff4d4f;">请先选择串口</span>'; 
        return; 
    }
    log.innerHTML = '<span style="color:#1890ff;">开始批量测试...</span><br>';
    
    cases.forEach((caseName, index) => {
        setTimeout(() => {
            runCase(ip, serial, caseName);
        }, index * 1000);
    });
}

function downloadReport() {
    const logContent = document.getElementById('logArea').textContent;
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_report_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function refreshHosts() {
    fetchHosts();
}

function showAddHostModal() {
    editingHostIndex = null;
    document.getElementById('modalTitle').textContent = '添加电脑';
    document.getElementById('hostForm').reset();
    document.getElementById('hostModal').style.display = 'block';
}

function editHost(index) {
    editingHostIndex = index;
    const host = hosts[index];
    document.getElementById('modalTitle').textContent = '编辑电脑';
    document.getElementById('hostIp').value = host.ip;
    document.getElementById('hostName').value = host.name;
    document.getElementById('hostLocation').value = host.location;
    document.getElementById('hostModal').style.display = 'block';
}

function closeHostModal() {
    document.getElementById('hostModal').style.display = 'none';
}

function deleteHost(ip) {
    if (!confirm('确定要删除这台电脑吗？')) return;
    
    fetch(`${API_BASE}/host/${ip}`, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert('删除成功');
            refreshHosts();
        } else {
            alert('删除失败: ' + data.message);
        }
    })
    .catch(error => {
        alert('删除失败: ' + error.message);
    });
}

document.getElementById('hostForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const hostData = {
        ip: formData.get('ip'),
        name: formData.get('name') || formData.get('ip'),
        location: formData.get('location') || '未知'
    };
    
    // IP地址验证
    const ipRegex = /^(\\d{1,3}\\.){3}\\d{1,3}$/;
    if (!ipRegex.test(hostData.ip)) {
        alert('请输入有效的IP地址');
        return;
    }
    
    const method = editingHostIndex !== null ? 'PUT' : 'POST';
    const url = editingHostIndex !== null ? `${API_BASE}/host/${hostData.ip}` : `${API_BASE}/hosts`;
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(hostData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(editingHostIndex !== null ? '更新成功' : '添加成功');
            closeHostModal();
            refreshHosts();
        } else {
            alert('操作失败: ' + data.message);
        }
    })
    .catch(error => {
        alert('操作失败: ' + error.message);
    });
});

// 自动刷新功能
document.getElementById('autoRefresh').addEventListener('change', function(e) {
    if (e.target.checked) {
        window.autoRefreshInterval = setInterval(refreshHosts, 30000);
    } else {
        clearInterval(window.autoRefreshInterval);
    }
});

// 初始化
fetchHosts();
    </script>
</body>
</html>
        '''
    
    def run(self, host: str = None, port: int = None, debug: bool = None):
        """运行Center API服务"""
        host = host or self.config.CENTER_HOST
        port = port or self.config.CENTER_PORT
        debug = debug if debug is not None else self.config.DEBUG
        
        self.logger.info(f"启动Center API服务: {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)