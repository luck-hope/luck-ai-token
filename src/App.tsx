/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { WidgetMode, SessionItem, TaskItem, ProviderConfig, ThemeMode, TrackingTarget } from './types';
import { INITIAL_SESSIONS, INITIAL_TASKS, INITIAL_PROVIDERS } from './mockData';
import { FloatingWidget } from './components/FloatingWidget';
import { ProviderSettingsModal } from './components/ProviderSettingsModal';
import { SessionDetailDrawer } from './components/SessionDetailDrawer';
import { PythonCodeModal } from './components/PythonCodeModal';
import { MacAdaptationModal } from './components/MacAdaptationModal';
import {
  CircleDot,
  Minimize2,
  Maximize2,
  Play,
  Settings,
  Code,
  Zap,
  Sun,
  Moon,
  Apple,
  Pin,
  Sparkles,
  Layers,
} from 'lucide-react';

export default function App() {
  // 1. Theme state: 'dark' | 'light' (默认开启深色黑夜模式，高对比清晰字体与层次)
  const [theme, setTheme] = useState<ThemeMode>('dark');
  const isDark = theme === 'dark';

  // 同步 dark 类到 html 根节点，确保所有 Tailwind 变体及原生样式生效
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  // 2. macOS Style Mode Toggle
  const [isMacStyle, setIsMacStyle] = useState<boolean>(true);
  const [isMacModalOpen, setIsMacModalOpen] = useState<boolean>(false);

  // 3. Widget display state: 'circle' | 'capsule' | 'expanded' (默认展开完整监控面板)
  const [widgetMode, setWidgetMode] = useState<WidgetMode>('expanded');

  // 4. Gateway data state
  const [sessions, setSessions] = useState<SessionItem[]>(INITIAL_SESSIONS);
  const [tasks, setTasks] = useState<TaskItem[]>(INITIAL_TASKS);
  const [providers, setProviders] = useState<ProviderConfig[]>(INITIAL_PROVIDERS);
  const [port, setPort] = useState<number>(4000);

  // 5. Tracking target (Scheme 3: Auto-follow latest by default + Pin manual lock)
  const [trackingTarget, setTrackingTarget] = useState<TrackingTarget>({
    type: 'turn',
    id: INITIAL_TASKS[0]?.id || '',
    isAuto: true,
  });

  // Selected item for Detail Drawer (supports both TaskItem and SessionItem)
  const [detailItem, setDetailItem] = useState<SessionItem | TaskItem | null>(null);

  // Modals
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [isPythonCodeOpen, setIsPythonCodeOpen] = useState<boolean>(false);

  // Streaming simulation state
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamProgressText, setStreamProgressText] = useState<string>('');

  const handleResetDefaultSessions = () => {
    setSessions(INITIAL_SESSIONS);
    setTasks(INITIAL_TASKS);
    setTrackingTarget({ type: 'turn', id: INITIAL_TASKS[0]?.id || '', isAuto: true });
  };

  const handleClearAllSessions = () => {
    setSessions([]);
    setTasks([]);
    setTrackingTarget({ type: 'turn', id: '', isAuto: true });
    setDetailItem(null);
  };

  // Aggregated metrics
  const totalRequests = tasks.reduce((acc, t) => acc + t.requestCount, 0);
  const totalSessions = sessions.length;
  const overallCacheHitRate =
    tasks.length > 0
      ? tasks.reduce((acc, t) => acc + t.cacheHitRate, 0) / tasks.length
      : 0;

  // Compute active task for capsule display
  const activeTask: TaskItem = (() => {
    if (!trackingTarget.isAuto && trackingTarget.id) {
      const found = tasks.find((t) => t.id === trackingTarget.id);
      if (found) return found;
    }
    return tasks[0] || {
      id: 'empty',
      taskNum: 0,
      name: '暂无活跃请求',
      sessionId: 'none',
      sessionNum: 0,
      requestCount: 0,
      successRequestCount: 0,
      provider: 'openai',
      inputTokens: 0,
      outputTokens: 0,
      totalTokens: 0,
      cacheHitRate: 0,
      cacheHitTokens: 0,
      model: 'none',
      costCny: 0,
      savedCny: 0,
      createdAt: '--:--',
    };
  })();

  const activeSession: SessionItem = (() => {
    const matched = sessions.find((s) => s.id === activeTask.sessionId);
    return matched || sessions[0] || {
      id: 'sess-empty',
      sessionNum: 0,
      taskCount: 0,
      requestCount: 0,
      successRequestCount: 0,
      title: '暂无活跃会话',
      provider: 'openai',
      inputTokens: 0,
      outputTokens: 0,
      totalTokens: 0,
      cacheHitRate: 0,
      cacheHitTokens: 0,
      model: 'none',
      costCny: 0,
      savedCny: 0,
      createdAt: '--:--',
      requests: [],
    };
  })();

  // Navigation across tasks from capsule
  const handlePrevTask = () => {
    const currentIndex = tasks.findIndex((t) => t.id === activeTask.id);
    if (currentIndex < tasks.length - 1) {
      const nextOne = tasks[currentIndex + 1];
      setTrackingTarget({ type: 'turn', id: nextOne.id, isAuto: false });
    }
  };

  const handleNextTask = () => {
    const currentIndex = tasks.findIndex((t) => t.id === activeTask.id);
    if (currentIndex > 0) {
      const prevOne = tasks[currentIndex - 1];
      setTrackingTarget({ type: 'turn', id: prevOne.id, isAuto: false });
    }
  };

  // Simulate an incoming streaming request
  const handleSimulateRequest = () => {
    if (isStreaming) return;
    setIsStreaming(true);

    const testPool = [
      {
        provider: 'deepseek',
        model: 'deepseek-coder',
        prompt: '优化 FastAPI 异步网关的长连接复用，避免在 macOS 环境下出现 socket 泄漏',
      },
      {
        provider: 'sensenova',
        model: 'sensenova-v5-pro',
        prompt: '提取用户首条 user 提示词前 18 个字符并生成自适应悬浮胶囊标题',
      },
      {
        provider: 'bigmodel',
        model: 'glm-4-flash',
        prompt: '解析智谱 GLM 流式结束帧中的 prompt_tokens 与 cached_tokens 注入字段',
      },
    ];
    const picked = testPool[Math.floor(Math.random() * testPool.length)];
    setStreamProgressText(`[${picked.provider}] 流式转发中: ${picked.prompt.slice(0, 15)}...`);

    let currentTokens = 0;
    const interval = setInterval(() => {
      currentTokens += 10;
      if (currentTokens >= 60) {
        clearInterval(interval);
        setIsStreaming(false);
        setStreamProgressText('');

        const newId = `turn-${Date.now()}`;
        const hitRate = +(72 + Math.random() * 22).toFixed(1);
        const inTok = 50 + Math.floor(Math.random() * 20);
        const outTok = 30 + Math.floor(Math.random() * 20);
        const totalTok = inTok + outTok;

        const newTask: TaskItem = {
          id: newId,
          taskNum: tasks.length + 1,
          name: picked.prompt.slice(0, 24) + '...',
          sessionId: 'sess-3',
          sessionNum: 3,
          requestCount: 1,
          successRequestCount: 1,
          provider: picked.provider,
          inputTokens: inTok,
          outputTokens: outTok,
          totalTokens: totalTok,
          cacheHitRate: hitRate,
          cacheHitTokens: Math.round((inTok * hitRate) / 100),
          model: picked.model,
          costCny: +(totalTok * 0.0001).toFixed(3),
          savedCny: +((totalTok * 0.0003) * (hitRate / 100)).toFixed(3),
          ttftMs: Math.round(180 + Math.random() * 70),
          createdAt: new Date().toLocaleTimeString(),
          userPromptSnippet: picked.prompt,
        };

        setTasks([newTask, ...tasks]);

        // 如果用户是自动追踪模式，胶囊条立即切换为最新任务；如果已锁定某历史任务，则不打扰当前展示！
        if (trackingTarget.isAuto) {
          setTrackingTarget({ type: 'turn', id: newTask.id, isAuto: true });
        }
      }
    }, 120);
  };

  return (
    <div
      className={`relative w-screen h-screen overflow-hidden font-sans select-none transition-colors duration-200 ${
        isDark ? 'dark bg-[#0c0f16] text-zinc-100' : 'bg-[#f4f5f8] text-zinc-800'
      }`}
    >
      {/* Background IDE / Code Editor Atmosphere */}
      <div className={`absolute inset-0 flex flex-col pointer-events-none ${isDark ? 'opacity-30' : 'opacity-20'}`}>
        <div
          className={`h-8 border-b flex items-center px-4 gap-4 text-xs font-mono ${
            isDark ? 'bg-[#151922] border-zinc-800 text-zinc-500' : 'bg-white border-zinc-200 text-zinc-500'
          }`}
        >
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500/60" />
            <span className="w-3 h-3 rounded-full bg-amber-500/60" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/60" />
          </div>
          <span>gateway_proxy.py — VS Code / Cursor IDE (AI Token Monitor)</span>
          <span className="ml-auto">UTF-8 · Python 3.11 · Port {port}</span>
        </div>

        <div className="flex-1 p-6 font-mono text-xs text-zinc-500 leading-relaxed overflow-hidden">
          <div># 本地用量中转代理与悬浮窗数据协议 (FastAPI + PySide6)</div>
          <div className="text-purple-400">from fastapi import FastAPI, Request</div>
          <div className="text-purple-400">from fastapi.responses import StreamingResponse</div>
          <div className="mt-2 text-zinc-600"># 提取首会话标题并向桌面悬浮胶囊广播当前任务与 Prompt 命中率</div>
          <div className="text-blue-400">async def broadcast_capsule_state(turn_info: dict):</div>
          <div className="pl-4 text-zinc-400">floating_widget.emit_turn(turn_info)</div>
        </div>
      </div>

      {/* Top Floating Control Bar */}
      <header
        className={`relative z-30 flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 border-b text-xs shadow-md transition-colors ${
          isDark
            ? 'bg-[#12151e]/90 backdrop-blur-md border-zinc-800'
            : 'bg-white/90 backdrop-blur-md border-zinc-200 shadow-xs'
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(74,222,128,0.8)]" />
            <span className="font-semibold text-sm tracking-wide">
              轻量用量网关 · 悬浮交互原型
            </span>
          </div>

          <div
            className={`hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] ${
              isDark ? 'bg-zinc-800/80 text-zinc-400' : 'bg-zinc-100 text-zinc-600'
            }`}
          >
            <span>监听端口:</span>
            <span className="text-sky-500 font-mono font-medium">127.0.0.1:{port}</span>
          </div>
        </div>

        {/* Middle Mode Switch Buttons */}
        <div
          className={`flex items-center gap-1 p-1 rounded-xl border ${
            isDark ? 'bg-[#1a1f2c] border-zinc-700/60' : 'bg-zinc-100 border-zinc-300'
          }`}
        >
          <button
            type="button"
            onClick={() => setWidgetMode('circle')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs transition-colors ${
              widgetMode === 'circle'
                ? 'bg-sky-500 text-white font-medium shadow-xs'
                : isDark
                ? 'text-zinc-400 hover:text-zinc-200'
                : 'text-zinc-600 hover:text-zinc-900'
            }`}
            title="极简微标 (绿色环形仪表+呼吸点)"
          >
            <CircleDot className="w-3.5 h-3.5" />
            <span>极简微标</span>
          </button>

          <button
            type="button"
            onClick={() => setWidgetMode('capsule')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs transition-colors ${
              widgetMode === 'capsule'
                ? 'bg-sky-500 text-white font-medium shadow-xs'
                : isDark
                ? 'text-zinc-400 hover:text-zinc-200'
                : 'text-zinc-600 hover:text-zinc-900'
            }`}
            title="椭圆胶囊条 (当前任务首会话标题+服务商标+总Token+命中率)"
          >
            <Minimize2 className="w-3.5 h-3.5" />
            <span>椭圆胶囊</span>
          </button>

          <button
            type="button"
            onClick={() => setWidgetMode('expanded')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs transition-colors ${
              widgetMode === 'expanded'
                ? 'bg-sky-500 text-white font-medium shadow-xs'
                : isDark
                ? 'text-zinc-400 hover:text-zinc-200'
                : 'text-zinc-600 hover:text-zinc-900'
            }`}
            title="展开网关监控与任务便签面板"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span>展开面板</span>
          </button>
        </div>

        {/* Right Action Tools: Theme + Mac Style + Simulation + Code */}
        <div className="flex items-center gap-2">
          {/* Day / Night Theme Toggle */}
          <button
            type="button"
            onClick={() => setTheme(isDark ? 'light' : 'dark')}
            title={isDark ? '切换为白天浅色模式' : '切换为夜间深色模式'}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
              isDark
                ? 'bg-zinc-800 hover:bg-zinc-700 text-amber-300 border-zinc-700'
                : 'bg-white hover:bg-zinc-100 text-amber-600 border-zinc-300'
            }`}
          >
            {isDark ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
            <span className="hidden md:inline">{isDark ? '浅色白天' : '深色夜间'}</span>
          </button>

          {/* Mac Compatibility Toggle */}
          <button
            type="button"
            onClick={() => setIsMacModalOpen(true)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
              isMacStyle
                ? 'bg-sky-500/15 text-sky-400 border-sky-500/40'
                : isDark
                ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border-zinc-700'
                : 'bg-white hover:bg-zinc-100 text-zinc-700 border-zinc-300'
            }`}
            title="查看 macOS 原生支持与兼容建议"
          >
            <Apple className="w-3.5 h-3.5" />
            <span className="hidden md:inline">macOS 适配</span>
          </button>

          {/* Simulate Stream Button */}
          <button
            type="button"
            onClick={handleSimulateRequest}
            disabled={isStreaming}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium transition-all shadow-[0_0_12px_rgba(16,185,129,0.3)] text-xs"
          >
            <Play className={`w-3.5 h-3.5 ${isStreaming ? 'animate-spin' : ''}`} />
            <span>{isStreaming ? '流式中...' : '模拟请求'}</span>
          </button>

          {/* Python Code Modal Trigger */}
          <button
            type="button"
            onClick={() => setIsPythonCodeOpen(true)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border font-medium transition-colors text-xs ${
              isDark
                ? 'bg-zinc-800 hover:bg-zinc-700 text-sky-300 border-sky-500/30'
                : 'bg-white hover:bg-zinc-100 text-sky-600 border-zinc-300'
            }`}
            title="查看 Python 源码实现"
          >
            <Code className="w-3.5 h-3.5" />
            <span className="hidden lg:inline">Python 源码</span>
          </button>

          {/* Settings */}
          <button
            type="button"
            onClick={() => setIsSettingsOpen(true)}
            className={`p-1.5 rounded-lg border transition-colors ${
              isDark
                ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border-zinc-700'
                : 'bg-white hover:bg-zinc-100 text-zinc-600 border-zinc-300'
            }`}
            title="服务商与路由设置"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Real-time streaming status floating toast */}
      {isStreaming && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-950/90 border border-emerald-500/40 text-emerald-300 text-xs shadow-lg backdrop-blur-xs animate-bounce">
          <Zap className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
          <span>{streamProgressText}</span>
        </div>
      )}

      {/* Floating Interactive Widget (Draggable) */}
      <FloatingWidget
        mode={widgetMode}
        onModeChange={setWidgetMode}
        sessions={sessions}
        tasks={tasks}
        port={port}
        totalRequests={totalRequests}
        totalSessions={totalSessions}
        overallCacheHitRate={overallCacheHitRate}
        currentSession={activeSession}
        currentTask={activeTask}
        isStreaming={isStreaming}
        onSelectSession={(sess) => setDetailItem(sess)}
        onSelectTask={(task) => setDetailItem(task)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isMacStyle={isMacStyle}
        theme={theme}
        onToggleTheme={() => setTheme(isDark ? 'light' : 'dark')}
        trackingTarget={trackingTarget}
        onSetTrackingTarget={setTrackingTarget}
        onPrevTask={handlePrevTask}
        onNextTask={handleNextTask}
        onUnlockTracking={() => setTrackingTarget({ type: 'turn', id: '', isAuto: true })}
        onTriggerTurn={handleSimulateRequest}
      />

      {/* Bottom helper tip */}
      <footer className="absolute bottom-3 left-4 right-4 z-20 flex flex-wrap items-center justify-between text-xs pointer-events-none">
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border backdrop-blur-xs ${
            isDark ? 'bg-[#12151e]/80 border-zinc-800 text-zinc-400' : 'bg-white/80 border-zinc-200 text-zinc-600'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-sky-400" />
          <span>
            当前展示: <strong>{activeTask.name}</strong> ({activeTask.provider}) ·{' '}
            {trackingTarget.isAuto ? '⚡ 自动追踪最新请求' : '📌 已手动锁定该任务'}
          </span>
        </div>
        <div
          className={`px-3 py-1.5 rounded-lg border backdrop-blur-xs text-[11px] font-mono ${
            isDark ? 'bg-[#12151e]/80 border-zinc-800 text-zinc-400' : 'bg-white/80 border-zinc-200 text-zinc-600'
          }`}
        >
          总 Token: <strong className="text-sky-400">{activeTask.totalTokens}</strong> · 命中率:{' '}
          <strong className="text-emerald-400">{activeTask.cacheHitRate.toFixed(1)}%</strong>
        </div>
      </footer>

      {/* Modals & Drawers */}
      <ProviderSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        providers={providers}
        onSaveProviders={setProviders}
        port={port}
        onUpdatePort={setPort}
        onClearAllSessions={handleClearAllSessions}
        onResetDefaultSessions={handleResetDefaultSessions}
      />

      <SessionDetailDrawer
        item={detailItem}
        onClose={() => setDetailItem(null)}
        theme={theme}
        trackingTarget={trackingTarget}
        onSetTrackingTarget={setTrackingTarget}
      />

      <PythonCodeModal
        isOpen={isPythonCodeOpen}
        onClose={() => setIsPythonCodeOpen(false)}
      />

      <MacAdaptationModal
        isOpen={isMacModalOpen}
        onClose={() => setIsMacModalOpen(false)}
      />
    </div>
  );
}
