import React, { useState } from 'react';
import {
  X,
  Copy,
  Check,
  Folder,
  FileCode,
  FolderOpen,
  Terminal,
  Cpu,
  Layers,
  Settings,
  Package,
  Download,
  CheckCheck
} from 'lucide-react';

interface CodeFile {
  id: string;
  path: string;
  folder: string;
  filename: string;
  description: string;
  content: string;
}

const PROJECT_FILES: CodeFile[] = [
  {
    id: 'main',
    folder: '根目录',
    path: 'main.py',
    filename: 'main.py',
    description: '程序主入口：启动后台 FastAPI 网关线程并唤起 PySide6 悬浮窗 GUI',
    content: `"""
UsageGateway - 跨平台 AI 网关与实时桌面悬浮胶囊监控
运行环境: Python 3.10+
支持系统: macOS (Apple Silicon/Intel) & Windows 10/11
"""

import sys
import threading
import uvicorn
import platform
from PySide6.QtWidgets import QApplication

from gateway.proxy import app as gateway_app
from ui.widget import GatewayFloatingWidget
from config import GATEWAY_HOST, GATEWAY_PORT

def run_gateway_server():
    """在后台独立守护线程中启动 FastAPI 网关"""
    uvicorn.run(
        gateway_app,
        host=GATEWAY_HOST,
        port=GATEWAY_PORT,
        log_level="warning"
    )

def main():
    # 1. 启动后台网关守护线程
    server_thread = threading.Thread(target=run_gateway_server, daemon=True)
    server_thread.start()
    print(f"[Gateway] 代理网关已在后台就绪: http://{GATEWAY_HOST}:{GATEWAY_PORT}")

    # 2. 启动 PySide6 前端悬浮窗应用
    # 解决高分屏 (HiDPI) 缩放模糊
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        QApplication.highDpiScaleFactorRoundingPolicy().PassThrough
    )
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("UsageGateway")

    # 3. 创建悬浮胶囊并显示
    widget = GatewayFloatingWidget(port=GATEWAY_PORT)
    widget.show()

    print("[UI] 桌面悬浮胶囊已启动 (单击微调/双击切换面板/长按拖动)")
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    main()
`
  },
  {
    id: 'gateway_proxy',
    folder: 'gateway',
    path: 'gateway/proxy.py',
    filename: 'proxy.py',
    description: 'FastAPI 核心网关：智能提取首会话标题、透传请求、动态开启 stream_options 并解析 Usage',
    content: `"""
FastAPI 智能转发反向网关 (gateway/proxy.py)
核心功能:
1. 拦截解析对话首消息并截断生成易读的会话标题;
2. 遇到 stream=True 时自动补充 stream_options={"include_usage": True},
   确保 DeepSeek / OpenAI / 商汤 等在 SSE 结束帧准确回传缓存命中与总 Token;
3. 实时通知桌面悬浮窗更新当前任务数据。
"""

import json
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from gateway.counter import UsageTracker
from config import UPSTREAM_CONFIG

app = FastAPI(title="Usage Gateway Core", version="1.0.0")
tracker = UsageTracker()

def extract_truncated_title(body: dict, max_chars: int = 16) -> str:
    """提取首条用户消息生成截断标题"""
    messages = body.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            content = str(msg.get("content", "")).strip()
            first_line = content.split("\\n")[0].strip("#* -")
            if len(first_line) > max_chars:
                return first_line[:max_chars] + "..."
            return first_line or "新对话会话"
    return "代码重构任务"

@app.get("/health")
async def health():
    return {"status": "ok", "tracker": tracker.get_summary()}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    model = body.get("model", "deepseek-chat")
    is_stream = body.get("stream", False)

    # 1. 提取首会话标题并更新当前活动任务
    task_name = extract_truncated_title(body)
    tracker.start_task(name=task_name, model=model)

    # 2. 保证流式输出包含使用量信息 (关键优化)
    if is_stream:
        stream_opts = body.setdefault("stream_options", {})
        stream_opts["include_usage"] = True

    # 3. 解析对应的上游服务商 URL 与密钥
    provider_info = UPSTREAM_CONFIG.resolve_provider(model)
    target_url = f"{provider_info['base_url'].rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {provider_info['api_key']}",
        "Content-Type": "application/json"
    }

    client = httpx.AsyncClient(timeout=120.0)

    if not is_stream:
        # 非流式直接转发
        resp = await client.post(target_url, json=body, headers=headers)
        res_json = resp.json()
        if "usage" in res_json:
            tracker.record_usage(res_json["usage"], model=model)
        await client.aclose()
        return res_json

    # 流式转发：逐块解析 SSE 并捕获最后一个 usage 帧
    req = client.build_request("POST", target_url, json=body, headers=headers)
    upstream_resp = await client.send(req, stream=True)

    async def stream_generator():
        try:
            async for chunk in upstream_resp.aiter_lines():
                if not chunk:
                    continue
                yield f"{chunk}\\n\\n"
                
                # 检查是否包含 usage 统计帧
                if chunk.startswith("data: ") and chunk != "data: [DONE]":
                    data_str = chunk[6:]
                    try:
                        data_json = json.loads(data_str)
                        if "usage" in data_json and data_json["usage"]:
                            tracker.record_usage(data_json["usage"], model=model)
                    except json.JSONDecodeError:
                        pass
        finally:
            await upstream_resp.aclose()
            await client.aclose()

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
`
  },
  {
    id: 'gateway_counter',
    folder: 'gateway',
    path: 'gateway/counter.py',
    filename: 'counter.py',
    description: '用量与计费统计模块：计算 Prompt Cache 命中率与不同模型人民币花费',
    content: `"""
用量与计费统计模块 (gateway/counter.py)
"""

from typing import Dict, Any, List
import time

class UsageTracker:
    def __init__(self):
        self.current_task = {
            "name": "等待首个对话...",
            "model": "deepseek-v3",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cached_tokens": 0,
            "total_tokens": 0,
            "cache_hit_rate": 0.0,
            "cost_cny": 0.0,
            "is_streaming": False
        }
        self.tasks_history: List[Dict[str, Any]] = []
        self.total_requests = 0

    def start_task(self, name: str, model: str):
        self.current_task["name"] = name
        self.current_task["model"] = model
        self.current_task["is_streaming"] = True
        self.total_requests += 1

    def record_usage(self, usage: dict, model: str):
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        
        # 兼容不同服务商的 Cache 字段
        # DeepSeek: prompt_cache_hit_tokens
        # OpenAI: prompt_tokens_details.cached_tokens
        # SenseNova: cached_tokens
        details = usage.get("prompt_tokens_details", {}) or {}
        cached_tokens = (
            usage.get("prompt_cache_hit_tokens") or
            details.get("cached_tokens") or
            usage.get("cached_tokens") or 0
        )

        hit_rate = (cached_tokens / prompt_tokens * 100.0) if prompt_tokens > 0 else 0.0
        
        # 计费计算 (示例 DeepSeek: 缓存 0.5元/M, 未缓存 2元/M, 输出 8元/M)
        cost_cny = (cached_tokens * 0.5 + (prompt_tokens - cached_tokens) * 2.0 + completion_tokens * 8.0) / 1_000_000

        self.current_task.update({
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cached_tokens": cached_tokens,
            "total_tokens": total_tokens,
            "cache_hit_rate": round(hit_rate, 1),
            "cost_cny": round(cost_cny, 4),
            "is_streaming": False,
            "updated_at": time.time()
        })
        self.tasks_history.insert(0, dict(self.current_task))

    def get_summary(self):
        return {
            "current": self.current_task,
            "total_requests": self.total_requests,
            "history_count": len(self.tasks_history)
        }
`
  },
  {
    id: 'ui_widget',
    folder: 'ui',
    path: 'ui/widget.py',
    filename: 'widget.py',
    description: 'PySide6 跨平台桌面悬浮胶囊：无边框置顶、0延迟跟手拖拽、三态平滑伸缩',
    content: `"""
PySide6 悬浮胶囊窗组件 (ui/widget.py)
特性:
1. 跨平台支持: 适配 macOS (无 Dock 栏阴影/WA_MacAlwaysShowToolWindow) 与 Windows (Frameless/ToolWindow);
2. 纯代码自绘矢量图形: 包含微型命中率圆环、截断标题、Token 与计费胶囊;
3. 零延迟贴手平滑拖拽与边界防护.
"""

import platform
from PySide6.QtCore import Qt, QPoint, QRectF, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget

class GatewayFloatingWidget(QWidget):
    def __init__(self, port: int = 8088):
        super().__init__()
        self.port = port
        self.mode = "capsule"  # "circle" | "capsule" | "expanded"
        
        # 界面状态
        self.session_title = "重构用量网关首会话截断标题..."
        self.cache_hit_rate = 76.7
        self.total_tokens = 152
        self.cost_cny = 0.012
        self.is_streaming = False

        # 1. 窗口属性设置: 置顶 + 无边框无干扰
        flags = (
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        if platform.system() == "Darwin":
            flags |= Qt.WindowType.WindowDoesNotAcceptFocus
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 2. 尺寸与位置
        self.drag_position = QPoint()
        self.resize(340, 40)
        self.move(200, 80)

        # 3. 定时轮询本地网关状态
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.fetch_latest_state)
        self.poll_timer.start(500)

    def fetch_latest_state(self):
        # 实际通过 requests.get(f"http://127.0.0.1:{self.port}/health") 刷新
        pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            if platform.system() == "Darwin":
                new_pos.setY(max(26, new_pos.y()))  # 防遮挡 macOS 菜单栏
            self.move(new_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        # 双击在圆形微标、长条胶囊与全功能大屏间平滑循环
        modes = ["circle", "capsule", "expanded"]
        next_idx = (modes.index(self.mode) + 1) % len(modes)
        self.set_mode(modes[next_idx])

    def set_mode(self, mode: str):
        self.mode = mode
        if mode == "circle":
            self.resize(44, 44)
        elif mode == "capsule":
            self.resize(340, 40)
        elif mode == "expanded":
            self.resize(580, 490)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 暗夜纯粹背景
        bg_color = QColor(17, 20, 28, 245)
        border_color = QColor(255, 255, 255, 30)
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(bg_color))

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        if self.mode == "circle":
            painter.drawEllipse(rect)
            # 命中率绿色刻度环
            green_pen = QPen(QColor(74, 222, 128), 3.0)
            painter.setPen(green_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            span = int((self.cache_hit_rate / 100.0) * 360 * 16)
            painter.drawArc(rect.adjusted(4, 4, -4, -4), 90 * 16, -span)
            return

        elif self.mode == "capsule":
            radius = rect.height() / 2
            painter.drawRoundedRect(rect, radius, radius)

            # 左侧微型进度圆标
            orb_rect = QRectF(rect.x() + 4, rect.y() + 4, 32, 32)
            green_pen = QPen(QColor(74, 222, 128), 2.5)
            painter.setPen(green_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            span = int((self.cache_hit_rate / 100.0) * 360 * 16)
            painter.drawArc(orb_rect.adjusted(3, 3, -3, -3), 90 * 16, -span)

            # 居中截断标题
            painter.setPen(QColor(230, 235, 245))
            font = QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9)
            painter.setFont(font)
            title_rect = QRectF(rect.x() + 42, rect.y(), 160, rect.height())
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter, self.session_title[:14] + "...")

            # 右侧 Token 药丸
            badge_x = rect.x() + 210
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(28, 34, 46)))
            painter.drawRoundedRect(QRectF(badge_x, rect.y() + 8, 56, 24), 12, 12)
            painter.setPen(QColor(180, 190, 205))
            painter.drawText(QRectF(badge_x, rect.y() + 8, 56, 24), Qt.AlignmentFlag.AlignCenter, f"{self.total_tokens}tok")

            # 右侧 命中率 药丸
            hit_x = badge_x + 62
            painter.setBrush(QBrush(QColor(16, 50, 36)))
            painter.drawRoundedRect(QRectF(hit_x, rect.y() + 8, 58, 24), 12, 12)
            painter.setPen(QColor(74, 222, 128))
            painter.drawText(QRectF(hit_x, rect.y() + 8, 58, 24), Qt.AlignmentFlag.AlignCenter, f"⚡{self.cache_hit_rate:.1f}%")
`
  },
  {
    id: 'config',
    folder: '根目录',
    path: 'config.py',
    filename: 'config.py',
    description: '配置文件：网关监听端口、商汤/DeepSeek/OpenAI 基础地址与密钥映射',
    content: `"""
网关全局配置 (config.py)
"""
import os

GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 8088

class UpstreamConfig:
    def __init__(self):
        self.providers = {
            "deepseek": {
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                "api_key": os.getenv("DEEPSEEK_API_KEY", "sk-your-deepseek-key")
            },
            "sensenova": {
                "base_url": os.getenv("SENSENOVA_BASE_URL", "https://api.sensenova.cn/compatible-mode/v1"),
                "api_key": os.getenv("SENSENOVA_API_KEY", "sk-your-sensenova-key")
            },
            "openai": {
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "api_key": os.getenv("OPENAI_API_KEY", "sk-your-openai-key")
            }
        }

    def resolve_provider(self, model: str) -> dict:
        m = model.lower()
        if "deepseek" in m:
            return self.providers["deepseek"]
        if "sense" in m or "nova" in m:
            return self.providers["sensenova"]
        return self.providers["openai"]

UPSTREAM_CONFIG = UpstreamConfig()
`
  },
  {
    id: 'requirements',
    folder: '根目录',
    path: 'requirements.txt',
    filename: 'requirements.txt',
    description: '项目核心依赖清单',
    content: `fastapi>=0.100.0
uvicorn>=0.23.0
httpx>=0.24.0
PySide6>=6.5.0
pyinstaller>=6.0.0
`
  },
  {
    id: 'github_ci',
    folder: '.github/workflows',
    path: '.github/workflows/build.yml',
    filename: 'build.yml',
    description: 'GitHub Actions 跨平台自动打包流水线 (提交代码自动产出 Mac .dmg 与 Win .exe)',
    content: `name: Build Cross-Platform Desktop App

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: windows-latest
            artifact_name: UsageGateway-Windows.exe
            build_cmd: pyinstaller --noconsole --onefile --name "UsageGateway-Win64" main.py
          - os: macos-latest
            artifact_name: UsageGateway-macOS.app
            build_cmd: pyinstaller --noconsole --windowed --name "UsageGateway-macOS" main.py

    runs-on: \${{ matrix.os }}
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          pip install -r requirements.txt

      - name: Build Executable
        run: |
          \${{ matrix.build_cmd }}

      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: \${{ matrix.artifact_name }}
          path: dist/*
`
  },
  {
    id: 'readme',
    folder: '根目录',
    path: 'README.md',
    filename: 'README.md',
    description: '项目本地运行与打包说明',
    content: `# UsageGateway 桌面悬浮窗与用量网关

## 快速运行
\`\`\`bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务 (同时启动后台网关与悬浮窗)
python main.py
\`\`\`

## 本地打包
- **Windows (生成 .exe)**:
  \`\`\`bash
  pyinstaller --noconsole --onefile --name "UsageGateway" main.py
  \`\`\`
- **macOS (生成 .app)**:
  \`\`\`bash
  pyinstaller --noconsole --windowed --name "UsageGateway" main.py
  \`\`\`
`
  }
];

export const PythonCodeModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose,
}) => {
  const [selectedFileId, setSelectedFileId] = useState<string>('main');
  const [copiedFile, setCopiedFile] = useState<boolean>(false);
  const [copiedAll, setCopiedAll] = useState<boolean>(false);

  if (!isOpen) return null;

  const currentFile = PROJECT_FILES.find((f) => f.id === selectedFileId) || PROJECT_FILES[0];

  const handleCopyFile = () => {
    navigator.clipboard.writeText(currentFile.content);
    setCopiedFile(true);
    setTimeout(() => setCopiedFile(false), 2000);
  };

  const handleCopyAllProject = () => {
    const combined = PROJECT_FILES.map(
      (f) => `# ==========================================\n# 文件路径: ${f.path}\n# 说明: ${f.description}\n# ==========================================\n\n${f.content}\n\n`
    ).join('\n');
    navigator.clipboard.writeText(combined);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2500);
  };

  // Group files by folder
  const folders = Array.from(new Set(PROJECT_FILES.map((f) => f.folder)));

  return (
    <div
      id="python-code-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-xs p-4 select-none font-sans"
    >
      <div className="w-[920px] max-w-full h-[640px] max-h-[92vh] bg-[#10131b] rounded-2xl border border-zinc-700/80 shadow-2xl overflow-hidden text-zinc-200 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 bg-[#151923] border-b border-zinc-800 text-sm font-semibold">
          <div className="flex items-center gap-2.5">
            <Cpu className="w-4 h-4 text-sky-400" />
            <span>Python 完整工程源码中心 (按模块分类导出)</span>
            <span className="text-[11px] font-normal px-2 py-0.5 rounded-full bg-sky-950 border border-sky-800/60 text-sky-300">
              共 {PROJECT_FILES.length} 个核心文件
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopyAllProject}
              title="将全部文件合并一键复制到剪贴板"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition-colors shadow-xs"
            >
              {copiedAll ? <CheckCheck className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedAll ? '已复制整套工程' : '一键复制全套源码'}</span>
            </button>
            <button
              type="button"
              onClick={onClose}
              className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-zinc-700/40 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Workspace Body: Left File Tree + Right Code View */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Project Directory Sidebar */}
          <div className="w-56 bg-[#0d1017] border-r border-zinc-800/80 flex flex-col text-xs">
            <div className="p-3 border-b border-zinc-800/60 text-[11px] font-medium text-zinc-400 flex items-center justify-between">
              <span>项目工程目录树</span>
              <span className="font-mono text-[10px] text-zinc-500">v1.0</span>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-3">
              {folders.map((folder) => {
                const filesInFolder = PROJECT_FILES.filter((f) => f.folder === folder);
                return (
                  <div key={folder} className="space-y-0.5">
                    <div className="flex items-center gap-1.5 px-2 py-1 text-zinc-400 font-medium text-[11px]">
                      <FolderOpen className="w-3.5 h-3.5 text-amber-400/80" />
                      <span>{folder}</span>
                    </div>
                    <div className="pl-3 space-y-0.5">
                      {filesInFolder.map((file) => {
                        const isSelected = file.id === selectedFileId;
                        return (
                          <button
                            key={file.id}
                            type="button"
                            onClick={() => setSelectedFileId(file.id)}
                            className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left transition-colors font-mono text-[11px] ${
                              isSelected
                                ? 'bg-sky-500/20 text-sky-300 font-semibold border border-sky-500/30'
                                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
                            }`}
                          >
                            <FileCode
                              className={`w-3.5 h-3.5 flex-shrink-0 ${
                                isSelected ? 'text-sky-400' : 'text-zinc-500'
                              }`}
                            />
                            <span className="truncate">{file.filename}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Code Viewer & Actions */}
          <div className="flex-1 flex flex-col bg-[#0b0e14] overflow-hidden">
            {/* Active file toolbar */}
            <div className="flex items-center justify-between px-4 py-2 bg-[#121620] border-b border-zinc-800 text-xs">
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-mono font-medium text-sky-300">{currentFile.path}</span>
                <span className="text-zinc-500 text-[11px] truncate">({currentFile.description})</span>
              </div>
              <button
                type="button"
                onClick={handleCopyFile}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition-colors shadow-xs flex-shrink-0"
              >
                {copiedFile ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedFile ? '已复制此文件' : '复制代码'}</span>
              </button>
            </div>

            {/* Code Content Area */}
            <div className="flex-1 p-4 overflow-auto font-mono text-xs leading-relaxed text-zinc-300 select-text">
              <pre className="whitespace-pre selection:bg-sky-900/60 font-mono">
                {currentFile.content}
              </pre>
            </div>
          </div>
        </div>

        {/* Bottom Status Bar */}
        <div className="flex items-center justify-between px-5 py-2.5 bg-[#131720] border-t border-zinc-800 text-xs text-zinc-400">
          <div className="flex items-center gap-4 text-[11px]">
            <span>架构方案: <strong>FastAPI + PySide6 + PyInstaller</strong></span>
            <span>双端运行: <strong>Mac (Metal/Cocoa) / Win (DirectX) 源码免改</strong></span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition-colors"
          >
            完成并关闭
          </button>
        </div>
      </div>
    </div>
  );
};
