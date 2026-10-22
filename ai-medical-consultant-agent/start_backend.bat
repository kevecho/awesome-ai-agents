@echo off
chcp 65001 >nul
echo ============================================
echo   AI Medical Consultant - 后端启动脚本
echo ============================================
echo.

cd /d "%~dp0backend"

echo [1/3] 安装依赖...
pip install -r requirements.txt

echo.
echo [2/3] 初始化医学知识库...
python -m data.medical_kb.init_kb

echo.
echo [3/3] 启动FastAPI服务...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
