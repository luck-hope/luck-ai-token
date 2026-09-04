# TokenTrackerGateway (Desktop & Web)

> 🚀 **打开即用的跨平台 AI Token 监控与桌面原生置顶悬浮窗** (macOS / Windows / Linux)。
> 随时常驻桌面，**开箱即用（直连主方案，无需前置配置网关）**，同时支持 **可选的本地代理网关扩展接入**。
> 支持 **三态无缝切换（微型圆标 Orb / 椭圆摘要胶囊 CapsuleBar / 全量网关大屏 Full Panel）**，实时统计 Token 消耗、Prompt 缓存命中率与多模型计费。

---

## ✨ 核心特性

- 🖥️ **桌面原生置顶悬浮窗 (打开即用 · PySide6 / Qt)**：
  - **打开直接可用**：无需强制配置任何外部 IDE 插件或前置网关，启动软件即可直接进行 Token 消耗监控、会话任务管理与直接测试。
  - **无边框置顶 & 零延迟跟手拖拽**：原生跨平台无干扰窗口，智能避开 macOS 菜单栏与 Windows 任务栏。
  - **三态无缝切换**：
    1. 🟢 **微型圆标 (Mini Orb)**：44px 紧凑圆形，外圈动态展示 Prompt Cache 命中率光环；
    2. 💊 **椭圆摘要胶囊 (CapsuleBar)**：展示首会话截断标题、请求数、Token 总量与命中率；
    3. 📊 **全量网关大屏 (Full Panel)**：包含任务列表、服务商图标、会话明细、排序筛选与分页。
  - **多维快捷交互**：支持双击切换形态、右键快捷菜单、Esc 快速折叠、W/A/S/D 与方向键滑动列表。
  - **系统常驻托盘 (System Tray)**：暗夜翠绿雷电托盘图标，支持一键显隐与安全退出。

- ⚡ **扩展本地转发网关 (可选辅助方案 · FastAPI / Uvicorn)**：
  - 本地后台静默监听 `http://127.0.0.1:4000/v1`，供有外部代理需求的用户将 IDE / 客户端（Cursor, VS Code, Cline 等）指向本地网关。
  - **流式 Usage 自动提取**：自动注入 `stream_options: {"include_usage": true}`，精准捕获 DeepSeek / OpenAI / 商汤 / 智谱 等在流式输出结束帧中的 Prompt Cache 命中数据与 Token 消耗。

---

## 📦 快速开始 (桌面原生版)

### 方式一：一键脚本运行 (推荐)

- **macOS / Linux**：
  ```bash
  git clone https://github.com/luck-hope/luck-ai-token.git
  cd luck-ai-token
  chmod +x start.sh
  ./start.sh
  ```

- **Windows**：
  ```cmd
  git clone https://github.com/luck-hope/luck-ai-token.git
  cd luck-ai-token
  双击运行 start.bat
  ```

### 方式二：手动 Python 运行

```bash
# 1. 创建并激活虚拟环境 (Python 3.10+)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动桌面应用与后台网关
python main.py
```

### 方式三：独立打包为可执行程序 (.exe / .app)

```bash
python build_exe.py
# 生成文件位于 dist/ 目录下：
# - Windows: dist/TokenTrackerGateway.exe
# - macOS:   dist/TokenTrackerGateway.app
```

---

## 🛠️ IDE 客户端接入方法

在您的 IDE（如 Cursor、VS Code 插件、Cline）或 API 工具中配置：

- **API Base URL**：`http://127.0.0.1:4000/v1`
- **API Key**：可填任意占位符（如 `sk-local-test`）
- **Model**：填写支持的模型名称（如 `deepseek-coder`, `o3-mini`, `sensenova-v5-5`, `glm-4-flash`）

发起对话后，桌面悬浮胶囊将立即实时更新 Token 计数与缓存命中率！

---

## 📂 项目结构

```
├── main.py                  # 桌面原生程序主入口 (PySide6 + 托盘管理器)
├── config.py                # 网关端口、服务商与上游路由规则配置
├── requirements.txt         # Python 核心依赖清单 (FastAPI, PySide6, Uvicorn, httpx)
├── start.sh / start.bat     # macOS / Linux / Windows 一键启动脚本
├── build_exe.py             # PyInstaller 一键打包可执行程序脚本
├── gateway/                 # 后台网关模块
│   ├── proxy.py             # FastAPI 反向代理与流式 Usage 拦截解析
│   └── counter.py           # Token / 缓存命中率 / 计费统计器
├── ui/                      # 桌面原生界面模块
│   └── widget.py            # PySide6 悬浮窗 (支持圆标、胶囊、全量大屏三态自绘)
└── src/                     # Web 互动体验版源码 (React + Vite + TailwindCSS)
```

---

## 📄 开源许可

MIT License
