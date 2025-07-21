@echo off
echo 🚀 推送项目到GitHub
echo ==================
echo.

echo 📝 请按照以下步骤操作：
echo.

echo 1. 获取GitHub Personal Access Token:
echo    - 访问 https://github.com/settings/tokens
echo    - 点击 "Generate new token (classic)"
echo    - 勾选 "repo" 权限
echo    - 复制生成的token
echo.

echo 2. 设置远程仓库URL（包含token）:
echo    git remote set-url origin https://KSHHH1:YOUR_TOKEN@github.com/KSHHH1/Enterprise-Test-Platform.git
echo    （请将 YOUR_TOKEN 替换为您的实际token）
echo.

echo 3. 推送代码:
echo    git push -u origin main
echo.

echo 🔒 注意：token是敏感信息，请妥善保管！
echo.

pause