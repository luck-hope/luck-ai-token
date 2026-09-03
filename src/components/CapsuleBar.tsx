import React from 'react';
import { MiniOrb } from './MiniOrb';
import {
  ChevronRight,
  ChevronLeft,
  Minimize2,
  Sparkles,
  Zap,
  Coins,
  Pin,
  RefreshCw,
  Sun,
  Moon,
} from 'lucide-react';
import { ProviderBadge } from '../utils/providerBadge';
import { ThemeMode, TrackingTarget } from '../types';

interface CapsuleBarProps {
  sessionTitle: string;
  cacheHitRate: number;
  totalTokens: number;
  costCny: number;
  requestCount?: number;
  successRequestCount?: number;
  provider?: string;
  isStreaming?: boolean;
  onExpand: () => void;
  onShrinkToCircle: () => void;
  showCost?: boolean;
  onToggleCostType?: () => void;
  isMacStyle?: boolean;
  theme?: ThemeMode;
  onToggleTheme?: () => void;
  trackingTarget?: TrackingTarget;
  onPrevTask?: () => void;
  onNextTask?: () => void;
  onUnlockTracking?: () => void;
}

export const CapsuleBar: React.FC<CapsuleBarProps> = ({
  sessionTitle,
  cacheHitRate,
  totalTokens,
  costCny,
  requestCount = 1,
  successRequestCount,
  provider = 'deepseek',
  isStreaming = false,
  onExpand,
  onShrinkToCircle,
  showCost = false,
  onToggleCostType,
  isMacStyle = false,
  theme = 'dark',
  onToggleTheme,
  trackingTarget,
  onPrevTask,
  onNextTask,
  onUnlockTracking,
}) => {
  const isDark = theme === 'dark';

  return (
    <div
      id="gateway-capsule-bar"
      className={`group relative flex items-center h-10 pl-1.5 pr-2 py-1 rounded-full border transition-all duration-300 select-none cursor-pointer max-w-[500px] shadow-xl ${
        isDark
          ? isMacStyle
            ? 'bg-[#141822]/95 hover:bg-[#181d2a]/95 text-zinc-100 border-white/15 shadow-[0_8px_30px_rgba(0,0,0,0.6)] backdrop-blur-md'
            : 'bg-[#11141c]/95 hover:bg-[#151923]/95 text-zinc-100 border-sky-400/25 shadow-[0_8px_24px_rgba(0,0,0,0.5)] backdrop-blur-md'
          : 'bg-white/95 hover:bg-zinc-50/95 text-zinc-800 border-zinc-300 shadow-[0_8px_24px_rgba(0,0,0,0.12)] backdrop-blur-md'
      }`}
    >
      {/* 1. Left mini orb indicator */}
      <div
        className="flex-shrink-0"
        title="单击收缩为微型圆标"
        onClick={(e) => {
          e.stopPropagation();
          onShrinkToCircle();
        }}
      >
        <MiniOrb
          cacheHitRate={cacheHitRate}
          isStreaming={isStreaming}
          size={32}
          showTooltip={false}
        />
      </div>

      {/* 2. Provider Badge */}
      <div className="ml-1.5 flex-shrink-0" onClick={onExpand}>
        <ProviderBadge provider={provider} size="sm" />
      </div>

      {/* 3. Center: Task Switcher + Title */}
      <div
        className="flex items-center gap-1 mx-2 min-w-0 flex-1 overflow-hidden"
        onClick={onExpand}
        title={`当前查看任务: ${sessionTitle}\n点击展开完整监控面板`}
      >
        {/* Quick Prev Task */}
        {onPrevTask && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onPrevTask();
            }}
            title="查看上一个任务"
            className={`p-0.5 rounded-full transition-colors ${
              isDark ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200' : 'hover:bg-zinc-200 text-zinc-500'
            }`}
          >
            <ChevronLeft className="w-3 h-3" />
          </button>
        )}

        {/* Tracking status icon */}
        {trackingTarget && !trackingTarget.isAuto ? (
          <span
            title="已锁定该历史任务 (点击解除锁定，自动追踪最新)"
            onClick={(e) => {
              e.stopPropagation();
              if (onUnlockTracking) onUnlockTracking();
            }}
            className="flex-shrink-0 flex items-center gap-0.5 px-1 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[9px] font-mono cursor-pointer"
          >
            <Pin className="w-2.5 h-2.5 text-amber-400 fill-amber-400" />
            <span>定</span>
          </span>
        ) : isStreaming ? (
          <span className="flex-shrink-0 w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        ) : (
          <Sparkles className="w-3 h-3 text-sky-400 flex-shrink-0 opacity-70" />
        )}

        {/* Truncated Title */}
        <span
          className={`text-xs font-semibold truncate tracking-wide ${
            isDark ? 'text-white' : 'text-zinc-950 font-bold'
          }`}
        >
          {sessionTitle || '等待首个请求...'}
        </span>

        {/* Quick Next Task */}
        {onNextTask && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onNextTask();
            }}
            title="查看下一个任务"
            className={`p-0.5 rounded-full transition-colors ${
              isDark ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200' : 'hover:bg-zinc-200 text-zinc-500'
            }`}
          >
            <ChevronRight className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* 4. Right side: Requests pill + Token/Cost pill + Cache Hit pill + Controls */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        {/* Request count pill */}
        <div
          title={`当前任务/会话累计请求次数: ${requestCount} 次 (有效成功: ${successRequestCount ?? requestCount} 次)`}
          className={`hidden sm:flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[11px] font-mono font-medium border ${
            isDark
              ? 'bg-zinc-800/70 border-zinc-700/60 text-zinc-300'
              : 'bg-zinc-100 border-zinc-300 text-zinc-700'
          }`}
        >
          <span className="text-[10px] text-zinc-400 font-sans">请求</span>
          <span className="font-bold">{successRequestCount ?? requestCount}</span>
          {requestCount !== (successRequestCount ?? requestCount) && (
            <span className="text-[10px] text-zinc-500">/{requestCount}</span>
          )}
        </div>

        {/* Token / Cost toggleable pill (保留总Token, 点击切金额) */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            if (onToggleCostType) onToggleCostType();
          }}
          title="点击切换: 总 Token / 预估计费"
          className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono transition-colors border ${
            isDark
              ? 'bg-[#191f2c] border-zinc-700/60 text-zinc-200 hover:text-white hover:border-zinc-500'
              : 'bg-zinc-100 border-zinc-300 text-zinc-700 hover:bg-zinc-200 hover:text-zinc-900'
          }`}
        >
          {showCost ? (
            <>
              <Coins className="w-2.5 h-2.5 text-amber-400" />
              <span>¥{costCny.toFixed(3)}</span>
            </>
          ) : (
            <>
              <span className={`font-sans text-[10px] ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>tok</span>
              <span>{totalTokens}</span>
            </>
          )}
        </button>

        {/* Cache hit rate pill */}
        <div
          title={`Prompt 缓存命中率: ${cacheHitRate.toFixed(1)}%`}
          className={`flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[11px] font-mono font-medium border ${
            isDark
              ? 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300'
              : 'bg-emerald-50 border-emerald-300 text-emerald-700'
          }`}
        >
          <Zap className="w-2.5 h-2.5 text-emerald-500 fill-emerald-500/30" />
          <span>{cacheHitRate.toFixed(1)}%</span>
        </div>

        {/* Theme quick switcher */}
        {onToggleTheme && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onToggleTheme();
            }}
            title={isDark ? '切换为浅色白天模式' : '切换为深色夜间模式'}
            className={`p-1 rounded-full transition-colors ${
              isDark ? 'text-zinc-400 hover:text-amber-300 hover:bg-white/10' : 'text-zinc-500 hover:text-amber-600 hover:bg-zinc-200'
            }`}
          >
            {isDark ? <Sun className="w-3 h-3" /> : <Moon className="w-3 h-3" />}
          </button>
        )}

        {/* Minimize / Expand buttons */}
        <div className="flex items-center gap-0.5 ml-0.5">
          <button
            type="button"
            title="缩小为微型圆标"
            onClick={(e) => {
              e.stopPropagation();
              onShrinkToCircle();
            }}
            className={`p-1 rounded-full transition-colors ${
              isDark ? 'text-zinc-400 hover:text-zinc-200 hover:bg-white/10' : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-200'
            }`}
          >
            <Minimize2 className="w-3 h-3" />
          </button>
          <button
            type="button"
            title="展开网关监控面板"
            onClick={onExpand}
            className={`p-1 rounded-full transition-colors ${
              isDark ? 'text-zinc-400 hover:text-white hover:bg-white/10' : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-200'
            }`}
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
