# TokenTrackerGateway (Web)

> 轻量级大模型用量网关悬浮胶囊与监控面板，支持三态无缝切换：圆形 Orb / 椭圆摘要胶囊 / 全量网关面板。

## 功能

- **三态切换**：MiniOrb 圆形光标 ↔ CapsuleBar 摘要胶囊 ↔ FullGatewayPanel 完整面板
- **实时统计**：请求数、会话数、Token 消耗、Prompt 缓存命中率、TTFT 首字延迟
- **多服务商**：OpenAI / DeepSeek / SenseNova / GLM 等（ProviderSettingsModal 可配置）
- **任务管理**：任务列表 / 会话列表 / 详情抽屉，支持📌锁定至悬浮窗
- **IDE 接入**：本地 API 接入地址（如 `http://127.0.0.1:4000/v1`），W/A/S/D 或方向键平滑滚动
- **主题**：暗夜高对比 + 浅色主题切换

## 仓库

- **主页**：https://github.com/luck-hope/luck-ai-token
- **Release**：https://github.com/luck-hope/luck-ai-token/releases

## 安装 & 使用

### 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/luck-hope/luck-ai-token.git
cd luck-ai-token

# 2. 安装依赖
npm install

# 3. 配置环境变量（复制 .env.example 为 .env）
GEMINI_API_KEY="MY_GEMINI_API_KEY"

# 4. 启动
npm run dev
# → http://localhost:3000
```

### 生产构建

```bash
npm run build   # 产物在 dist/
npm run preview # 本地预览
```

## 项目结构

```
src/
  components/
    MiniOrb.tsx              圆形光标（三态之一）
    CapsuleBar.tsx           椭圆摘要胶囊（三态之二）
    FullGatewayPanel.tsx     全量网关面板（三态之三）
    SessionDetailDrawer.tsx  会话详情抽屉
    ProviderSettingsModal.tsx 服务商配置
    MacAdaptationModal.tsx   macOS 适配引导
  utils/
    providerBadge.tsx        服务商徽标
  mockData.ts                演示数据
  types.ts                   TS 类型定义
main.tsx / App.tsx           应用入口
```

## 接入方式

将 IDE / 客户端的 API Base URL 指向网关地址（如 `http://127.0.0.1:4000/v1`），请求完成后 Token 用量自动出现在面板中。

## 技术栈

React 19 + TypeScript + Vite 6 + TailwindCSS 4 + Lucide 图标 + Motion 动画

## License

MIT
