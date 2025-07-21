@echo off
echo 正在配置企业测试平台防火墙规则...
echo.

REM 添加中心服务端口5002的防火墙规则
netsh advfirewall firewall add rule name="Enterprise Test Platform Center" dir=in action=allow protocol=TCP localport=5002
if %errorlevel% equ 0 (
    echo ✓ 中心服务端口5002防火墙规则添加成功
) else (
    echo ✗ 中心服务端口5002防火墙规则添加失败
)

REM 添加代理服务端口5001的防火墙规则
netsh advfirewall firewall add rule name="Enterprise Test Platform Agent" dir=in action=allow protocol=TCP localport=5001
if %errorlevel% equ 0 (
    echo ✓ 代理服务端口5001防火墙规则添加成功
) else (
    echo ✗ 代理服务端口5001防火墙规则添加失败
)

echo.
echo 防火墙配置完成！
echo 现在其他电脑可以通过以下地址访问：
echo 中心服务: http://192.168.0.122:5002
echo.
pause