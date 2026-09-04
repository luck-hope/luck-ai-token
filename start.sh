#!/usr/bin/env bash
# TokenTrackerGateway 桌面原生应用一键启动脚本 (macOS / Linux)

set -e

echo "=== 正在检查 Python 运行环境 ==="
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3，请先安装 Python 3.10+ (https://www.python.org/)"
    exit 1
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建 Python 虚拟环境 .venv ..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "安装/更新依赖 ..."
pip install -r requirements.txt -q

echo "=== 🚀 正在启动 TokenTrackerGateway 桌面悬浮窗与本地网关 ==="
python3 main.py
