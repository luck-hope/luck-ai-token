import React, { useState, useMemo, useRef, useEffect } from 'react';
import { SessionItem, TaskItem, ThemeMode, TrackingTarget, ColumnVisibility } from '../types';
import { ProviderBadge } from '../utils/providerBadge';
import {
  Minimize2,
  CircleDot,
  Settings,
  X,
  Pin,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
  Calendar,
  CheckSquare,
  Sun,
  Moon,
  Zap,
  RotateCcw,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Clock,
  Sparkles,
  Copy,
  Check,
} from 'lucide-react';

interface FullGatewayPanelProps {
  sessions: SessionItem[];
  tasks: TaskItem[];
  port?: number;
  totalRequests: number;
  totalSessions: number;
  overallCacheHitRate: number;
  selectedSession: SessionItem | null;
  onSelectSession: (sess: SessionItem) => void;
  onSelectTask?: (task: TaskItem) => void;
  onCloseToCapsule: () => void;
  onCloseToCircle: () => void;
  onOpenSettings: () => void;
  isMacStyle?: boolean;
  theme?: ThemeMode;
  onToggleTheme?: () => void;
  trackingTarget?: TrackingTarget;
  onSetTrackingTarget?: (target: TrackingTarget) => void;
  customWidth?: number;
  customHeight?: number;
}

type SortField = 'none' | 'id' | 'tokens' | 'hitRate' | 'requests';
type SortOrder = 'asc' | 'desc';

export const FullGatewayPanel: React.FC<FullGatewayPanelProps> = ({
  sessions,
  tasks,
  port = 4000,
  totalRequests,
  totalSessions,
  overallCacheHitRate,
  selectedSession,
  onSelectSession,
  onSelectTask,
  onCloseToCapsule,
  onCloseToCircle,
  onOpenSettings,
  isMacStyle = false,
  theme = 'dark',
  onToggleTheme,
  trackingTarget,
  onSetTrackingTarget,
  customWidth = 580,
  customHeight = 490,
}) => {
  const isDark = theme === 'dark';
  const [activeTab, setActiveTab] = useState<'task' | 'session'>('task');
  const [todoNote, setTodoNote] = useState<string>('当前冲刺：重构流式 usage 提取及悬浮胶囊');
  const [isEditingTodo, setIsEditingTodo] = useState<boolean>(false);

  // 1. 日历处支持用户手动完全自由输入（非下拉框）
  const [inputDate, setInputDate] = useState<string>('2026-09-03');

  // 2. 排序状态：支持按「ID编号」「总消耗」「命中率」「请求数」正反序排序
  const [sortField, setSortField] = useState<SortField>('none');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // URL 复制成功反馈
  const [isCopiedUrl, setIsCopiedUrl] = useState<boolean>(false);

  const handleCopyIdeUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setIsCopiedUrl(true);
    setTimeout(() => setIsCopiedUrl(false), 2200);
  };

  // 列字段自定义筛选（默认展示请求数、总消耗、命中率、模型、任务标题）
  const [columns, setColumns] = useState<ColumnVisibility>({
    requestCount: true, // 请求数 / 有效请求数
    inputTokens: false,
    outputTokens: false,
    costCny: false,
    ttftMs: false,
    model: true,
  });
  const [isFilterPopoverOpen, setIsFilterPopoverOpen] = useState<boolean>(false);

  // 分页状态 (每页 8 条)
  const pageSize = 8;
  const [page, setPage] = useState<number>(1);

  // 切换 ID 编号排序
  const handleSortId = () => {
    if (sortField !== 'id') {
      setSortField('id');
      setSortOrder('asc'); // ID 默认从 1 到 N 升序
    } else if (sortOrder === 'asc') {
      setSortOrder('desc'); // 切换为 N 到 1 降序
    } else {
      setSortField('none');
    }
    setPage(1);
  };

  // 切换总消耗排序
  const handleSortTokens = () => {
    if (sortField !== 'tokens') {
      setSortField('tokens');
      setSortOrder('desc');
    } else if (sortOrder === 'desc') {
      setSortOrder('asc');
    } else {
      setSortField('none');
    }
    setPage(1);
  };

  // 切换命中率排序
  const handleSortHitRate = () => {
    if (sortField !== 'hitRate') {
      setSortField('hitRate');
      setSortOrder('desc');
    } else if (sortOrder === 'desc') {
      setSortOrder('asc');
    } else {
      setSortField('none');
    }
    setPage(1);
  };

  // 切换请求数排序
  const handleSortRequests = () => {
    if (sortField !== 'requests') {
      setSortField('requests');
      setSortOrder('desc');
    } else if (sortOrder === 'desc') {
      setSortOrder('asc');
    } else {
      setSortField('none');
    }
    setPage(1);
  };

  // 排序与筛选计算
  const sortedTasks = useMemo(() => {
    const list = [...tasks];
    if (sortField === 'id') {
      list.sort((a, b) => (sortOrder === 'desc' ? b.taskNum - a.taskNum : a.taskNum - b.taskNum));
    } else if (sortField === 'tokens') {
      list.sort((a, b) => (sortOrder === 'desc' ? b.totalTokens - a.totalTokens : a.totalTokens - b.totalTokens));
    } else if (sortField === 'hitRate') {
      list.sort((a, b) => (sortOrder === 'desc' ? b.cacheHitRate - a.cacheHitRate : a.cacheHitRate - b.cacheHitRate));
    } else if (sortField === 'requests') {
      list.sort((a, b) => (sortOrder === 'desc' ? b.requestCount - a.requestCount : a.requestCount - b.requestCount));
    }
    return list;
  }, [tasks, sortField, sortOrder]);

  const sortedSessions = useMemo(() => {
    const list = [...sessions];
    if (sortField === 'id') {
      list.sort((a, b) => (sortOrder === 'desc' ? b.sessionNum - a.sessionNum : a.sessionNum - b.sessionNum));
    } else if (sortField === 'tokens') {
      list.sort((a, b) => (sortOrder === 'desc' ? b.totalTokens - a.totalTokens : a.totalTokens - b.totalTokens));
    } else if (sortField === 'hitRate') {
      list.sort((a, b) => (sortOrder === 'desc' ? b.cacheHitRate - a.cacheHitRate : a.cacheHitRate - b.cacheHitRate));
    } else if (sortField === 'requests') {
      list.sort((a, b) => (sortOrder === 'desc' ? b.requestCount - a.requestCount : a.requestCount - b.requestCount));
    }
    return list;
  }, [sessions, sortField, sortOrder]);

  const currentList = activeTab === 'task' ? sortedTasks : sortedSessions;
  const totalPages = Math.max(1, Math.ceil(currentList.length / pageSize));
  const displayedItems = currentList.slice((page - 1) * pageSize, page * pageSize);

  const tableContainerRef = useRef<HTMLDivElement>(null);

  // 键盘方向键与 WASD 滚动支持 (当鼠标在窗口内或窗口激活时)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // 如果用户正在输入框输入内容 (比如改便签或输入日期)，不劫持按键
      const target = e.target as HTMLElement;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
        return;
      }

      const container = tableContainerRef.current;
      if (!container) return;

      const key = e.key.toLowerCase();
      const scrollStepY = 36; // 每次滚动一行约 36px
      const scrollStepX = 50;

      if (key === 'w' || key === 'arrowup') {
        container.scrollBy({ top: -scrollStepY, behavior: 'smooth' });
        e.preventDefault();
      } else if (key === 's' || key === 'arrowdown') {
        container.scrollBy({ top: scrollStepY, behavior: 'smooth' });
        e.preventDefault();
      } else if (key === 'a' || key === 'arrowleft') {
        container.scrollBy({ left: -scrollStepX, behavior: 'smooth' });
        e.preventDefault();
      } else if (key === 'd' || key === 'arrowright') {
        container.scrollBy({ left: scrollStepX, behavior: 'smooth' });
        e.preventDefault();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handlePinItem = (e: React.MouseEvent, type: 'turn' | 'session', id: string) => {
    e.stopPropagation();
    if (!onSetTrackingTarget) return;
    if (trackingTarget && !trackingTarget.isAuto && trackingTarget.id === id) {
      onSetTrackingTarget({ type: 'turn', id: '', isAuto: true });
    } else {
      onSetTrackingTarget({ type, id, isAuto: false });
    }
  };

  return (
    <div
      id="gateway-full-window"
      style={{
        width: `${customWidth}px`,
        height: `${customHeight}px`,
      }}
      className={`flex flex-col rounded-xl border transition-colors duration-150 select-none overflow-hidden shadow-2xl ${
        isDark
          ? isMacStyle
            ? 'dark bg-[#141720]/98 text-zinc-100 border-white/15'
            : 'dark bg-[#12151d]/98 text-zinc-100 border-zinc-700/70'
          : 'bg-white text-zinc-950 border-zinc-300 shadow-[0_12px_40px_rgba(0,0,0,0.15)] font-sans'
      }`}
    >
      {/* ── 1. Top Header Bar ── */}
      <div
        className={`flex items-center justify-between px-3.5 py-2.5 border-b text-xs flex-shrink-0 ${
          isDark ? 'bg-[#171b26] border-zinc-800' : 'bg-[#f4f6f9] border-zinc-200 text-zinc-800'
        }`}
      >
        {/* Left: Traffic lights or dot */}
        <div className="flex items-center gap-2">
          {isMacStyle ? (
            <div className="flex items-center gap-1.5 mr-1">
              <button
                type="button"
                onClick={onCloseToCapsule}
                title="关闭收起"
                className="w-3 h-3 rounded-full bg-rose-500 hover:bg-rose-600 transition-colors shadow-2xs"
              />
              <button
                type="button"
                onClick={onCloseToCircle}
                title="缩小为圆标"
                className="w-3 h-3 rounded-full bg-amber-500 hover:bg-amber-600 transition-colors shadow-2xs"
              />
              <button
                type="button"
                onClick={onCloseToCapsule}
                title="缩放为胶囊"
                className="w-3 h-3 rounded-full bg-emerald-500 hover:bg-emerald-600 transition-colors shadow-2xs"
              />
            </div>
          ) : (
            <span className="w-2.5 h-2.5 rounded-full bg-sky-500 shadow-[0_0_8px_rgba(56,189,248,0.8)]" />
          )}

          <span className="font-bold text-sm text-zinc-950 dark:text-zinc-100">用量网关</span>
          <span
            className={`px-1.5 py-0.5 rounded font-mono text-[11px] font-bold ${
              isDark ? 'bg-zinc-800 text-sky-300' : 'bg-sky-100 text-sky-800 border border-sky-200'
            }`}
          >
            :{port}
          </span>
          <span className={`text-[12px] ml-1 font-medium ${isDark ? 'text-zinc-400' : 'text-zinc-700'}`}>
            请求<strong className="font-mono ml-0.5 text-zinc-950 dark:text-zinc-100">{totalRequests}</strong> · 会话
            <strong className="font-mono ml-0.5 text-zinc-950 dark:text-zinc-100">{totalSessions}</strong> · 命中{' '}
            <strong className="text-emerald-600 dark:text-emerald-400 font-mono font-bold">
              {overallCacheHitRate.toFixed(1)}%
            </strong>
          </span>
        </div>

        {/* Right Tools: Theme + Settings + Shrink + Close */}
        <div className="flex items-center gap-1.5 text-zinc-400">
          {onToggleTheme && (
            <button
              type="button"
              onClick={onToggleTheme}
              title={isDark ? '切换浅色白天模式' : '切换深色夜间模式'}
              className={`p-1.5 rounded-lg transition-colors ${
                isDark ? 'hover:bg-zinc-800 text-amber-300' : 'hover:bg-zinc-200 text-amber-600'
              }`}
            >
              {isDark ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
            </button>
          )}
          <button
            type="button"
            onClick={onOpenSettings}
            title="服务商与模型路由设置"
            className={`flex items-center gap-1 px-2 py-1 rounded transition-colors text-xs font-semibold ${
              isDark ? 'hover:text-zinc-100 hover:bg-zinc-800' : 'hover:text-zinc-900 hover:bg-zinc-200 text-zinc-800'
            }`}
          >
            <Settings className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">设置</span>
          </button>
          <div className={`w-[1px] h-3.5 mx-0.5 ${isDark ? 'bg-zinc-700' : 'bg-zinc-300'}`} />
          <button
            type="button"
            onClick={onCloseToCapsule}
            title="收缩为椭圆胶囊"
            className={`p-1 rounded transition-colors ${
              isDark ? 'hover:text-zinc-100 hover:bg-zinc-800' : 'hover:text-zinc-900 hover:bg-zinc-200 text-zinc-700'
            }`}
          >
            <Minimize2 className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={onCloseToCircle}
            title="缩小为微标"
            className={`p-1 rounded transition-colors ${
              isDark ? 'hover:text-zinc-100 hover:bg-zinc-800' : 'hover:text-zinc-900 hover:bg-zinc-200 text-zinc-700'
            }`}
          >
            <CircleDot className="w-3.5 h-3.5" />
          </button>
          {!isMacStyle && (
            <button
              type="button"
              onClick={onCloseToCapsule}
              title="关闭窗口"
              className="hover:text-rose-500 p-1 rounded transition-colors text-zinc-600 dark:text-zinc-400"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* ── 2. TodoList 单行便签条 + 手动输入日历 ── */}
      <div
        className={`flex items-center gap-2.5 px-3 py-1.5 border-b text-xs relative flex-shrink-0 ${
          isDark
            ? 'bg-[#0f121a] border-zinc-800/80 text-zinc-200'
            : 'bg-[#edf1f7] border-zinc-300 text-zinc-900 font-medium'
        }`}
      >
        {/* 日历处：支持用户键盘直接手动输入任何日期，或点击辅助选择 */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <Calendar className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />
          <div className="relative flex items-center">
            <input
              type="text"
              value={inputDate}
              onChange={(e) => setInputDate(e.target.value)}
              placeholder="YYYY-MM-DD"
              title="可直接敲键盘手动输入/修改任何日期"
              className={`w-[105px] px-2 py-0.5 rounded text-[12px] font-mono font-bold outline-none border transition-colors ${
                isDark
                  ? 'bg-[#181c26] border-zinc-700 text-zinc-100 focus:border-sky-500'
                  : 'bg-white border-zinc-300 text-zinc-950 shadow-2xs focus:border-sky-600'
              }`}
            />
            {/* 快速重设为今天的小按钮 */}
            <button
              type="button"
              onClick={() => setInputDate('2026-09-03')}
              title="快速重设为今天"
              className={`ml-1 px-1.5 py-0.5 rounded text-[10px] font-bold border transition-colors ${
                isDark
                  ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border-zinc-700'
                  : 'bg-white hover:bg-zinc-100 text-zinc-700 border-zinc-300 shadow-2xs'
              }`}
            >
              今天
            </button>
          </div>
        </div>

        <div className={`w-[1px] h-3.5 ${isDark ? 'bg-zinc-800' : 'bg-zinc-300'}`} />

        {/* Todo Editable inline tag */}
        <div className="flex items-center gap-1.5 flex-1 min-w-0">
          <CheckSquare className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
          {isEditingTodo ? (
            <input
              type="text"
              value={todoNote}
              autoFocus
              onChange={(e) => setTodoNote(e.target.value)}
              onBlur={() => setIsEditingTodo(false)}
              onKeyDown={(e) => e.key === 'Enter' && setIsEditingTodo(false)}
              className={`w-full px-2 py-0.5 rounded border text-[12px] font-semibold outline-none ${
                isDark
                  ? 'bg-[#1b202c] border-sky-500/50 text-white'
                  : 'bg-white border-sky-600 text-zinc-950 shadow-2xs font-bold'
              }`}
            />
          ) : (
            <span
              onClick={() => setIsEditingTodo(true)}
              title="点击可内联编辑当前任务便签"
              className={`text-[12px] font-bold truncate cursor-pointer hover:underline py-0.5 ${
                isDark ? 'text-zinc-200 hover:text-white' : 'text-zinc-950 hover:text-sky-700'
              }`}
            >
              {todoNote || '(点击添加当前任务/待办便签...)'}
            </span>
          )}
        </div>

        {/* Filter popover trigger & Auto-tracking badge */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {trackingTarget && !trackingTarget.isAuto && (
            <button
              type="button"
              onClick={() => onSetTrackingTarget && onSetTrackingTarget({ type: 'turn', id: '', isAuto: true })}
              title="当前已锁定特定任务，点击恢复实时跟踪最新任务"
              className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-500/15 border border-amber-500/30 text-amber-600 dark:text-amber-300 text-[11px] font-bold hover:bg-amber-500/25 transition-colors"
            >
              <Pin className="w-2.5 h-2.5 fill-amber-500" />
              <span>已锁定</span>
              <RotateCcw className="w-2.5 h-2.5 ml-0.5" />
            </button>
          )}

          {/* Columns filter button */}
          <button
            type="button"
            onClick={() => setIsFilterPopoverOpen(!isFilterPopoverOpen)}
            title="自定义显示字段"
            className={`flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-bold transition-colors ${
              isFilterPopoverOpen
                ? 'bg-sky-500/20 text-sky-700 dark:text-sky-400 border-sky-500/40'
                : isDark
                ? 'bg-[#181d28] border-zinc-700/80 text-zinc-300 hover:text-white'
                : 'bg-white border-zinc-300 text-zinc-900 hover:bg-zinc-100 shadow-2xs'
            }`}
          >
            <SlidersHorizontal className="w-3 h-3" />
            <span>列筛选</span>
          </button>
        </div>

        {/* Filter dropdown Popover */}
        {isFilterPopoverOpen && (
          <div
            className={`absolute right-3 top-8 z-30 p-3 rounded-xl border shadow-2xl flex flex-col gap-2 w-48 text-xs ${
              isDark ? 'bg-[#161a24] border-zinc-700 text-zinc-100' : 'bg-white border-zinc-300 text-zinc-950 shadow-xl'
            }`}
          >
            <span className="font-bold text-[12px] text-zinc-600 dark:text-zinc-400 pb-1 border-b border-zinc-200 dark:border-zinc-700">
              自定义表格展示字段
            </span>
            <label className="flex items-center gap-2 cursor-pointer text-[12px] font-medium">
              <input
                type="checkbox"
                checked={columns.requestCount}
                onChange={(e) => setColumns({ ...columns, requestCount: e.target.checked })}
                className="rounded text-sky-600"
              />
              <span>请求数 (有效/成功次数)</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-[12px] font-medium">
              <input
                type="checkbox"
                checked={columns.inputTokens}
                onChange={(e) => setColumns({ ...columns, inputTokens: e.target.checked })}
                className="rounded text-sky-600"
              />
              <span>输入 Token (Input)</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-[12px] font-medium">
              <input
                type="checkbox"
                checked={columns.outputTokens}
                onChange={(e) => setColumns({ ...columns, outputTokens: e.target.checked })}
                className="rounded text-sky-600"
              />
              <span>输出 Token (Output)</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-[12px] font-medium">
              <input
                type="checkbox"
                checked={columns.costCny}
                onChange={(e) => setColumns({ ...columns, costCny: e.target.checked })}
                className="rounded text-sky-600"
              />
              <span>预估费用 (¥ CNY)</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-[12px] font-medium">
              <input
                type="checkbox"
                checked={columns.ttftMs}
                onChange={(e) => setColumns({ ...columns, ttftMs: e.target.checked })}
                className="rounded text-sky-600"
              />
              <span>首字耗时 (TTFT ms)</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-[12px] font-medium">
              <input
                type="checkbox"
                checked={columns.model}
                onChange={(e) => setColumns({ ...columns, model: e.target.checked })}
                className="rounded text-sky-600"
              />
              <span>模型型号 (Model)</span>
            </label>
            <button
              type="button"
              onClick={() => setIsFilterPopoverOpen(false)}
              className="mt-1 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white font-bold text-center text-[11px]"
            >
              确定
            </button>
          </div>
        )}
      </div>

      {/* ── 3. Tab Bar (任务 vs 会话) ── */}
      <div
        className={`flex items-center justify-between px-3.5 pt-2 pb-1 text-xs border-b flex-shrink-0 ${
          isDark ? 'bg-[#141720] border-zinc-800/80' : 'bg-white border-zinc-200'
        }`}
      >
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => {
              setActiveTab('task');
              setPage(1);
            }}
            className={`px-3 py-1 rounded-t-lg font-bold text-xs transition-all ${
              activeTab === 'task'
                ? isDark
                  ? 'bg-[#1c2230] text-sky-400 border-b-2 border-sky-400'
                  : 'bg-zinc-100 text-sky-700 border-b-2 border-sky-600 shadow-2xs'
                : isDark
                ? 'text-zinc-400 hover:text-zinc-200'
                : 'text-zinc-600 hover:text-zinc-950'
            }`}
          >
            任务列表 ({tasks.length})
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('session');
              setPage(1);
            }}
            className={`px-3 py-1 rounded-t-lg font-bold text-xs transition-all ${
              activeTab === 'session'
                ? isDark
                  ? 'bg-[#1c2230] text-sky-400 border-b-2 border-sky-400'
                  : 'bg-zinc-100 text-sky-700 border-b-2 border-sky-600 shadow-2xs'
                : isDark
                ? 'text-zinc-400 hover:text-zinc-200'
                : 'text-zinc-600 hover:text-zinc-950'
            }`}
          >
            会话列表 ({sessions.length})
          </button>
        </div>

        <div className="flex items-center gap-2">
          {sortField !== 'none' && (
            <button
              type="button"
              onClick={() => setSortField('none')}
              title="重置为默认时间排序"
              className="text-[11px] text-sky-600 hover:underline flex items-center gap-0.5"
            >
              <span>重置排序</span>
            </button>
          )}
          <span className={`text-[11px] font-medium ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
            单击行查看详情 · 点击 📌 锁定至悬浮窗
          </span>
        </div>
      </div>

      {/* ── 4. Table Body (支持总消耗排序、命中率排序，纯图标展示服务商，支持 WASD/方向键按键滑动) ── */}
      <div
        ref={tableContainerRef}
        tabIndex={0}
        title="支持鼠标滚轮或键盘 W/A/S/D / 方向键上下左右平滑滚动"
        className="flex-1 min-h-0 overflow-x-auto overflow-y-auto focus:outline-hidden"
      >
        <table className="w-full border-collapse text-left text-[13px] whitespace-nowrap">
          <thead
            className={`sticky top-0 z-10 border-b font-sans font-bold text-[13px] ${
              isDark ? 'bg-[#181c25] border-zinc-800 text-zinc-100' : 'bg-[#edf1f7] border-zinc-300 text-zinc-800'
            }`}
          >
            <tr>
              <th className="py-2.5 px-2 text-center w-8">📌</th>

              {/* 1. 会话/任务 ID 编号排序 */}
              <th
                onClick={handleSortId}
                title="点击按会话/任务编号排序 (升序 / 降序)"
                className={`py-2.5 px-2.5 text-right w-12 cursor-pointer select-none transition-colors group/sort ${
                  sortField === 'id'
                    ? 'text-sky-600 dark:text-sky-400 bg-sky-500/10'
                    : 'hover:text-sky-600 dark:hover:text-sky-300'
                }`}
              >
                <div className="inline-flex items-center justify-end gap-1">
                  <span>#</span>
                  {sortField === 'id' ? (
                    sortOrder === 'asc' ? (
                      <ArrowUp className="w-3.5 h-3.5 text-sky-600" />
                    ) : (
                      <ArrowDown className="w-3.5 h-3.5 text-sky-600" />
                    )
                  ) : (
                    <ArrowUpDown className="w-3 h-3 opacity-40 group-hover/sort:opacity-100" />
                  )}
                </div>
              </th>

              <th className="py-2.5 px-3 text-center">服务商</th>

              {/* 0. 请求数 / 有效请求数 */}
              {columns.requestCount && (
                <th
                  onClick={handleSortRequests}
                  title="点击按请求数排序 (降序 / 升序)"
                  className={`py-2.5 px-3 text-right cursor-pointer select-none transition-colors group/sort ${
                    sortField === 'requests'
                      ? 'text-sky-600 dark:text-sky-400 bg-sky-500/10'
                      : 'hover:text-sky-600 dark:hover:text-sky-300'
                  }`}
                >
                  <div className="inline-flex items-center gap-1">
                    <span>请求数</span>
                    {sortField === 'requests' ? (
                      sortOrder === 'desc' ? (
                        <ArrowDown className="w-3.5 h-3.5 text-sky-600" />
                      ) : (
                        <ArrowUp className="w-3.5 h-3.5 text-sky-600" />
                      )
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40 group-hover/sort:opacity-100" />
                    )}
                  </div>
                </th>
              )}

              {/* 1. 支持「总消耗」排序 */}
              <th
                onClick={handleSortTokens}
                title="点击按总消耗排序 (降序 / 升序)"
                className={`py-2.5 px-3 text-right cursor-pointer select-none transition-colors group/sort ${
                  sortField === 'tokens'
                    ? 'text-sky-600 dark:text-sky-400 bg-sky-500/10'
                    : 'hover:text-sky-600 dark:hover:text-sky-300'
                }`}
              >
                <div className="inline-flex items-center gap-1">
                  <span>总消耗</span>
                  {sortField === 'tokens' ? (
                    sortOrder === 'desc' ? (
                      <ArrowDown className="w-3.5 h-3.5 text-sky-600" />
                    ) : (
                      <ArrowUp className="w-3.5 h-3.5 text-sky-600" />
                    )
                  ) : (
                    <ArrowUpDown className="w-3 h-3 opacity-40 group-hover/sort:opacity-100" />
                  )}
                </div>
              </th>

              {columns.inputTokens && <th className="py-2.5 px-3 text-right">输入</th>}
              {columns.outputTokens && <th className="py-2.5 px-3 text-right">输出</th>}
              {columns.costCny && <th className="py-2.5 px-3 text-right">费用</th>}
              {columns.ttftMs && <th className="py-2.5 px-3 text-right">TTFT</th>}

              {/* 2. 支持「命中率」排序 */}
              <th
                onClick={handleSortHitRate}
                title="点击按 Prompt 缓存命中率排序 (降序 / 升序)"
                className={`py-2.5 px-3 text-right cursor-pointer select-none transition-colors group/sort ${
                  sortField === 'hitRate'
                    ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10'
                    : 'hover:text-emerald-600 dark:hover:text-emerald-300'
                }`}
              >
                <div className="inline-flex items-center gap-1">
                  <span>命中率</span>
                  {sortField === 'hitRate' ? (
                    sortOrder === 'desc' ? (
                      <ArrowDown className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <ArrowUp className="w-3.5 h-3.5 text-emerald-600" />
                    )
                  ) : (
                    <ArrowUpDown className="w-3 h-3 opacity-40 group-hover/sort:opacity-100" />
                  )}
                </div>
              </th>

              {columns.model && <th className="py-2.5 px-3">模型</th>}
              <th className="py-2.5 px-3 font-sans">
                {activeTab === 'task' ? '任务指令标题' : '首会话消息'}
              </th>
            </tr>
          </thead>
          <tbody className={`divide-y font-mono text-[13px] ${isDark ? 'divide-zinc-800/80' : 'divide-zinc-200'}`}>
            {activeTab === 'task'
              ? (displayedItems as TaskItem[]).map((task) => {
                  const isPinned = trackingTarget?.id === task.id;
                  const isHighHit = task.cacheHitRate >= 70;
                  return (
                    <tr
                      key={task.id}
                      onClick={() => onSelectTask && onSelectTask(task)}
                      className={`cursor-pointer transition-colors group ${
                        isPinned
                          ? isDark
                            ? 'bg-sky-950/40 hover:bg-sky-900/50'
                            : 'bg-sky-50/90 hover:bg-sky-100/90'
                          : isDark
                          ? 'hover:bg-[#1a202c]'
                          : 'hover:bg-[#f7f9fc]'
                      }`}
                    >
                      {/* Pin button */}
                      <td className="py-2.5 px-2 text-center" onClick={(e) => handlePinItem(e, 'turn', task.id)}>
                        <button
                          type="button"
                          title={isPinned ? '已锁定显示至胶囊 (点击解除)' : '点击将该任务锁定在悬浮胶囊展示'}
                          className={`p-1 rounded transition-colors ${
                            isPinned
                              ? 'text-amber-500 bg-amber-500/15'
                              : 'text-zinc-400 opacity-40 group-hover:opacity-100 hover:text-amber-500'
                          }`}
                        >
                          <Pin className={`w-3.5 h-3.5 ${isPinned ? 'fill-amber-500' : ''}`} />
                        </button>
                      </td>

                      {/* Number */}
                      <td className={`py-2.5 px-2.5 text-right font-bold ${isDark ? 'text-zinc-300' : 'text-zinc-600'}`}>
                        #{task.taskNum}
                      </td>

                      {/* 3. Provider Badge - 仅显示纯高清图标，鼠标移入展示完整名称 */}
                      <td className="py-2.5 px-3 text-center">
                        <ProviderBadge provider={task.provider} size="sm" />
                      </td>

                      {/* Request count */}
                      {columns.requestCount && (
                        <td className={`py-2.5 px-3 text-right font-medium ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>
                          <span
                            title={`当前任务总共执行了 ${task.requestCount} 次请求 (有效成功: ${task.successRequestCount ?? task.requestCount} 次)`}
                            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-mono font-bold ${
                              isDark ? 'bg-zinc-800/80 text-zinc-200' : 'bg-zinc-100 text-zinc-700'
                            }`}
                          >
                            <span className="text-emerald-500 font-bold">✓</span>
                            <span>{task.successRequestCount ?? task.requestCount}</span>
                            {task.requestCount !== (task.successRequestCount ?? task.requestCount) && (
                              <span className="text-[10px] text-zinc-500 font-normal">/{task.requestCount}</span>
                            )}
                          </span>
                        </td>
                      )}

                      {/* Total tokens */}
                      <td className={`py-2.5 px-3 text-right font-bold ${isDark ? 'text-sky-400' : 'text-sky-600'}`}>
                        {task.totalTokens} tok
                      </td>

                      {columns.inputTokens && (
                        <td className={`py-2.5 px-3 text-right font-medium ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>
                          {task.inputTokens}
                        </td>
                      )}
                      {columns.outputTokens && (
                        <td className={`py-2.5 px-3 text-right font-medium ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>
                          {task.outputTokens}
                        </td>
                      )}
                      {columns.costCny && (
                        <td className={`py-2.5 px-3 text-right font-bold ${isDark ? 'text-amber-400' : 'text-amber-600'}`}>
                          ¥{task.costCny.toFixed(3)}
                        </td>
                      )}
                      {columns.ttftMs && (
                        <td className={`py-2.5 px-3 text-right font-medium ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>
                          {task.ttftMs ? `${task.ttftMs}ms` : '-'}
                        </td>
                      )}

                      {/* Cache Hit rate */}
                      <td
                        className={`py-2.5 px-3 text-right font-bold ${
                          isHighHit
                            ? isDark ? 'text-emerald-400' : 'text-emerald-600'
                            : isDark ? 'text-zinc-200' : 'text-zinc-800'
                        }`}
                      >
                        {isHighHit && <Zap className="w-3 h-3 inline mr-0.5 text-emerald-500" />}
                        {task.cacheHitRate.toFixed(1)}%
                      </td>

                      {/* Model: 白偏灰一点点 (text-zinc-300 / text-slate-300)，与高亮纯白标题拉开层次 */}
                      {columns.model && (
                        <td className={`py-2.5 px-3 font-mono truncate max-w-[130px] ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
                          {task.model}
                        </td>
                      )}

                      {/* Title: 高亮纯白色 text-white，白天模式深黑 text-zinc-950 font-bold */}
                      <td className={`py-2.5 px-3 font-sans font-bold truncate max-w-[260px] ${isDark ? 'text-white' : 'text-zinc-950'}`}>
                        {task.name}
                      </td>
                    </tr>
                  );
                })
              : (displayedItems as SessionItem[]).map((sess) => {
                  const isPinned = trackingTarget?.id === sess.id;
                  const isHighHit = sess.cacheHitRate >= 70;
                  return (
                    <tr
                      key={sess.id}
                      onClick={() => onSelectSession(sess)}
                      className={`cursor-pointer transition-colors group ${
                        isPinned
                          ? isDark
                            ? 'bg-sky-950/40 hover:bg-sky-900/50'
                            : 'bg-sky-50/90 hover:bg-sky-100/90'
                          : isDark
                          ? 'hover:bg-[#1a202c]'
                          : 'hover:bg-[#f7f9fc]'
                      }`}
                    >
                      <td className="py-2.5 px-2 text-center" onClick={(e) => handlePinItem(e, 'session', sess.id)}>
                        <button
                          type="button"
                          title={isPinned ? '已锁定显示至胶囊 (点击解除)' : '点击将该会话锁定在悬浮胶囊展示'}
                          className={`p-1 rounded transition-colors ${
                            isPinned
                              ? 'text-amber-500 bg-amber-500/15'
                              : 'text-zinc-400 opacity-40 group-hover:opacity-100 hover:text-amber-500'
                          }`}
                        >
                          <Pin className={`w-3.5 h-3.5 ${isPinned ? 'fill-amber-500' : ''}`} />
                        </button>
                      </td>

                      <td className={`py-2.5 px-2.5 text-right font-bold ${isDark ? 'text-zinc-300' : 'text-zinc-600'}`}>
                        #{sess.sessionNum}
                      </td>

                      <td className="py-2.5 px-3 text-center">
                        <ProviderBadge provider={sess.provider} size="sm" />
                      </td>

                      {/* Request count */}
                      {columns.requestCount && (
                        <td className={`py-2.5 px-3 text-right font-medium ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>
                          <span
                            title={`当前会话总共累计 ${sess.requestCount} 次请求 (有效成功: ${sess.successRequestCount ?? sess.requestCount} 次)`}
                            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-mono font-bold ${
                              isDark ? 'bg-zinc-800/80 text-zinc-200' : 'bg-zinc-100 text-zinc-700'
                            }`}
                          >
                            <span className="text-emerald-500 font-bold">✓</span>
                            <span>{sess.successRequestCount ?? sess.requestCount}</span>
                            {sess.requestCount !== (sess.successRequestCount ?? sess.requestCount) && (
                              <span className="text-[10px] text-zinc-500 font-normal">/{sess.requestCount}</span>
                            )}
                          </span>
                        </td>
                      )}

                      <td className={`py-2.5 px-3 text-right font-bold ${isDark ? 'text-sky-400' : 'text-sky-600'}`}>
                        {sess.totalTokens} tok
                      </td>

                      {columns.inputTokens && (
                        <td className={`py-2.5 px-3 text-right font-medium ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>
                          {sess.inputTokens}
                        </td>
                      )}
                      {columns.outputTokens && (
                        <td className={`py-2.5 px-3 text-right font-medium ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>
                          {sess.outputTokens}
                        </td>
                      )}
                      {columns.costCny && (
                        <td className={`py-2.5 px-3 text-right font-bold ${isDark ? 'text-amber-400' : 'text-amber-600'}`}>
                          ¥{sess.costCny.toFixed(3)}
                        </td>
                      )}
                      {columns.ttftMs && (
                        <td className={`py-2.5 px-3 text-right font-medium ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>
                          -
                        </td>
                      )}

                      <td
                        className={`py-2.5 px-3 text-right font-bold ${
                          isHighHit
                            ? isDark ? 'text-emerald-400' : 'text-emerald-600'
                            : isDark ? 'text-zinc-200' : 'text-zinc-800'
                        }`}
                      >
                        {isHighHit && <Zap className="w-3 h-3 inline mr-0.5 text-emerald-500" />}
                        {sess.cacheHitRate.toFixed(1)}%
                      </td>

                      {columns.model && (
                        <td className={`py-2.5 px-3 font-mono truncate max-w-[130px] ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
                          {sess.model}
                        </td>
                      )}

                      <td className={`py-2.5 px-3 font-sans font-bold truncate max-w-[260px] ${isDark ? 'text-white' : 'text-zinc-950'}`}>
                        {sess.title}
                      </td>
                    </tr>
                  );
                })}
          </tbody>
        </table>
      </div>

      {/* ── 5. Bottom Status Footer with Light Pagination ── */}
      <div
        className={`flex items-center justify-between px-4 py-2 border-t text-[11px] flex-shrink-0 ${
          isDark ? 'bg-[#151922] border-zinc-800 text-zinc-400' : 'bg-[#f4f6f9] border-zinc-200 text-zinc-700 font-semibold'
        }`}
      >
        <div className="flex items-center gap-1.5">
          <span>接入:</span>
          {/* 用户点击 URL 自动复制 */}
          <button
            type="button"
            onClick={() => handleCopyIdeUrl(`http://127.0.0.1:${port}/v1`)}
            title={isCopiedUrl ? '已复制到剪贴板' : '点击复制接入 URL 地址'}
            className={`group inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-mono font-bold transition-all border cursor-pointer select-none ${
              isCopiedUrl
                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50 shadow-[0_0_8px_rgba(16,185,129,0.3)]'
                : isDark
                ? 'bg-emerald-950/40 hover:bg-emerald-900/60 text-emerald-400 border-emerald-800/50 hover:border-emerald-500/60'
                : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border-emerald-300'
            }`}
          >
            <span>http://127.0.0.1:{port}/v1</span>
            {isCopiedUrl ? (
              <Check className="w-3 h-3 text-emerald-400" />
            ) : (
              <Copy className="w-3 h-3 opacity-60 group-hover:opacity-100 transition-opacity" />
            )}
          </button>

          <span className="hidden sm:inline-flex items-center gap-1 text-[11px] text-zinc-500 dark:text-zinc-400 ml-1">
            · 支持按键滑动 <kbd className="px-1 py-0.2 rounded text-[10px] font-mono font-bold bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-300 dark:border-zinc-700">W/A/S/D</kbd> <kbd className="px-1 py-0.2 rounded text-[10px] font-mono font-bold bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-300 dark:border-zinc-700">↑↓←→</kbd>
          </span>
        </div>

        {/* Lightweight Pagination controls */}
        <div className="flex items-center gap-2 font-sans">
          <span>共 {currentList.length} 条</span>
          <div className="flex items-center gap-1 font-mono">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className={`p-1 rounded transition-colors disabled:opacity-30 ${
                isDark ? 'hover:bg-zinc-800 text-zinc-300' : 'hover:bg-zinc-200 text-zinc-700'
              }`}
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className={`px-1 font-bold ${isDark ? 'text-sky-400' : 'text-sky-600'}`}>
              {page} / {totalPages}
            </span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className={`p-1 rounded transition-colors disabled:opacity-30 ${
                isDark ? 'hover:bg-zinc-800 text-zinc-300' : 'hover:bg-zinc-200 text-zinc-700'
              }`}
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
