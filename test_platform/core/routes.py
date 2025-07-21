from flask import redirect, url_for, render_template, send_from_directory
from . import bp

@bp.route('/')
def index():
    # 根路径应该重定向到登录页面
    return redirect('/login.html')

@bp.route('/login')
def login():
    # 重定向到静态的 login.html 文件
    return redirect('/login.html')

@bp.route('/login.html')
def login_html():
    return send_from_directory('static', 'login.html')

@bp.route('/index.html')
def index_html():
    return send_from_directory('static', 'index.html') 