# 1. 使用本地已有的Python镜像作为基础
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# 2. 使用官方源，避免镜像源问题
# 如果需要使用国内镜像，可以尝试阿里云或网易镜像
# RUN sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# 3. 安装必要的编译工具、libpq-dev、Nginx 以及 Supervisor
RUN apt-get update && apt-get install -y build-essential libpq-dev nginx supervisor dos2unix && rm -rf /var/lib/apt/lists/*

# 复制新的Nginx配置文件和Supervisor配置文件
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 6. 复制Python依赖的离线包
COPY py-deps/ /app/py-deps/

# 7. 复制依赖定义文件
COPY requirements.txt requirements.txt

# 8. 从本地文件夹安装依赖，如果本地没有则回退到官方源
RUN pip install --find-links=/app/py-deps -r requirements.txt

# 复制依赖和应用代码
COPY . .
COPY entrypoint.sh /app/entrypoint.sh

# 解决Windows(CRLF)和Linux(LF)换行符不兼容的问题
RUN dos2unix /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 使用 heredoc 强行覆盖 login.html，确保其内容绝对正确
RUN <<EOF cat > /app/test_platform/static/login.html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - 企业级测试平台</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="login-container">
        <h2>设备登录</h2>
        <form id="loginForm">
            <input type="password" id="password" name="password" placeholder="请输入访问密码" required>
            <button type="submit">登录</button>
        </form>
        <div id="loginError" class="error-message" style="display: none;"></div>
    </div>
    <script>
        function getFingerprint() {
            let fingerprint = localStorage.getItem("device_fingerprint");
            if (!fingerprint) {
                fingerprint = "fp_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
                localStorage.setItem("device_fingerprint", fingerprint);
            }
            return fingerprint;
        }
        async function login(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            data.fingerprint = getFingerprint();
            const errorElement = document.getElementById("loginError");
            errorElement.style.display = "none";
            errorElement.textContent = "";
            try {
                const response = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data),
                });
                if (response.ok) {
                    const result = await response.json();
                    localStorage.setItem("jwt_token", result.access_token);
                    window.location.href = "/index.html";
                } else {
                    const errorData = await response.json();
                    errorElement.textContent = `登录失败: \${errorData.message || "未知错误"}`;
                    errorElement.style.display = "block";
                }
            } catch (error) {
                errorElement.textContent = "无法连接到登录服务器，请检查网络。";
                errorElement.style.display = "block";
            }
        }
        document.addEventListener("DOMContentLoaded", () => {
            const loginForm = document.getElementById("loginForm");
            if (loginForm) {
                loginForm.addEventListener("submit", login);
            }
        });
    </script>
</body>
</html>
EOF

# 10. 声明应用运行的端口
# EXPOSE 8000

# 11. 设置环境变量，确保 Python 能找到我们的模块
ENV PYTHONPATH "${PYTHONPATH}:/app"

# 12. 运行应用的命令
# CMD指令由entrypoint脚本的最后一行 `exec supervisord` 接管
# CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]