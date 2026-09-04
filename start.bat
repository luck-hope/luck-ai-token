@echo off
chcp 65001 >nul
title TokenTrackerGateway 桌面原生网关

echo ====================================================
echo 🚀 正在启动 TokenTrackerGateway 桌面悬浮窗应用
echo ====================================================

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 并勾选 Add to PATH
    pause
    exit /b 1
)

if not exist ".venv" (
    echo 创建 Python 虚拟环境 .venv ...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo 安装/检查核心依赖 ...
pip install -r requirements.txt -q

echo 正在运行主程序 ...
python main.py

pause
