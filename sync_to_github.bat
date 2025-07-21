@echo off
echo 🚀 同步项目到GitHub
echo ==================

echo 📝 请先在GitHub上创建名为 Enterprise-Test-Platform 的仓库
echo.

echo 🔗 添加远程仓库地址...
echo 请将下面的命令中的 YOUR_USERNAME 替换为您的GitHub用户名：
echo.
echo git remote add origin https://github.com/YOUR_USERNAME/Enterprise-Test-Platform.git
echo.

echo 📤 推送代码到GitHub...
echo git branch -M main
echo git push -u origin main
echo.

echo ✅ 完成后，您的项目将在以下地址可见：
echo https://github.com/YOUR_USERNAME/Enterprise-Test-Platform
echo.

pause