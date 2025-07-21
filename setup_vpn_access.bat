@echo off
echo 配置企业测试平台VPN访问规则...
echo.

echo 添加VPN网段防火墙规则...
netsh advfirewall firewall add rule name="Enterprise Test Platform VPN Access" dir=in action=allow protocol=TCP localport=5002 remoteip=192.168.20.0/24

echo 添加10.8.0.0网段防火墙规则...
netsh advfirewall firewall add rule name="Enterprise Test Platform VPN 10.8" dir=in action=allow protocol=TCP localport=5002 remoteip=10.8.0.0/24

echo 检查防火墙规则...
netsh advfirewall firewall show rule name="Enterprise Test Platform VPN Access"
netsh advfirewall firewall show rule name="Enterprise Test Platform VPN 10.8"

echo.
echo VPN访问配置完成！
echo 现在可以通过以下地址访问：
echo   http://10.8.0.30:5002
echo   http://192.168.0.122:5002
echo.
pause