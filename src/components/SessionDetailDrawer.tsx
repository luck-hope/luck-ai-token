import React, { useState } from 'react';
import { SessionItem, TaskItem, ThemeMode, TrackingTarget } from '../types';
import { ProviderBadge } from '../utils/providerBadge';
import { X, Zap, Coins, Clock, Copy, Check, Pin, Terminal, ArrowDownRight, Layers } from 'lucide-react';

interface DetailDrawerProps {
  item: SessionItem | TaskItem | null;
  itemType?: 'session' | 'task';
  onClose: () => void;
  theme?: ThemeMode;
  trackingTarget?: TrackingTarget;
  onSetTrackingTarget?: (target: TrackingTarget) => void;
}

export const SessionDetailDrawer: React.FC<DetailDrawerProps> = ({
  item,
  itemType = 'task',
  onClose,
  theme = 'dark',
  trackingTarget,
  onSetTrackingTarget,
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  if (!item) return null;

  const isDark = theme === 'dark';
  const isTask = 'sessionId' in item || itemType === 'task';
  const isPinned = trackingTarget?.id === item.id;

  const titleText = isTask ? (item as TaskItem).name : (item as SessionItem).title;
  const promptText =
    item.userPromptSnippet ||
    (isTask
      ? `优化 ${item.model} 在流式响应下的 Prompt 缓存命中率与上下文 token 复用...`
      : `用户指令：${titleText}`);

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(promptText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTogglePin = () => {
    if (!onSetTrackingTarget) return;
    if (isPinned) {
      onSetTrackingTarget({ type: 'turn', id: '', isAuto: true });
    } else {
      onSetTrackingTarget({ type: isTask ? 'turn' : 'session', id: item.id, isAuto: false });
    }
  };

  return (
    <div
      id="item-detail-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 select-none font-sans"
    >
      <div
        className={`w-[600px] max-w-full rounded-2xl border shadow-2xl overflow-hidden transition-all duration-200 ${
          isDark
            ? 'bg-[#131720] text-zinc-200 border-zinc-700/80 shadow-[0_20px_50px_rgba(0,0,0,0.8)]'
            : 'bg-white text-zinc-800 border-zinc-200 shadow-[0_20px_50px_rgba(0,0,0,0.15)]'
        }`}
      >
        {/* Header */}
        <div
          className={`flex items-center justify-between px-5 py-3.5 border-b text-sm font-semibold ${
            isDark ? 'bg-[#171b26] border-zinc-800' : 'bg-zinc-50 border-zinc-200'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <span
              className={`px-2 py-0.5 rounded font-mono text-xs ${
                isDark ? 'bg-sky-500/20 text-sky-400' : 'bg-sky-100 text-sky-700'
              }`}
            >
              {isTask ? `任务 #${(item as TaskItem).taskNum}` : `会话 #${(item as SessionItem).sessionNum}`}
            </span>
            <span>{isTask ? '任务 (Turn) 详细消耗与指令分析' : '会话 (Session) 综合统计'}</span>
          </div>

          <div className="flex items-center gap-2">
            {onSetTrackingTarget && (
              <button
                type="button"
                onClick={handleTogglePin}
                title={isPinned ? '已锁定在悬浮窗 (点击解除锁定)' : '锁定此项并在悬浮胶囊中追踪'}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium transition-colors ${
                  isPinned
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    : isDark
                    ? 'bg-zinc-800/80 text-zinc-300 border-zinc-700 hover:text-white'
                    : 'bg-zinc-100 text-zinc-700 border-zinc-300 hover:bg-zinc-200'
                }`}
              >
                <Pin className={`w-3 h-3 ${isPinned ? 'fill-amber-400' : ''}`} />
                <span>{isPinned ? '已锁定至胶囊' : '📌 锁定追踪'}</span>
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className={`p-1.5 rounded-lg transition-colors ${
                isDark ? 'text-zinc-400 hover:text-white hover:bg-zinc-700/40' : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-200'
              }`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto text-xs">
          {/* Main Title & Provider Card */}
          <div
            className={`p-3.5 rounded-xl border space-y-2 ${
              isDark ? 'bg-[#171b24] border-zinc-800' : 'bg-zinc-50 border-zinc-200'
            }`}
          >
            <div className="flex items-center justify-between text-[11px]">
              <div className="flex items-center gap-2">
                <ProviderBadge provider={item.provider} size="md" />
                <span
                  className={`font-mono px-2 py-0.5 rounded text-[10px] ${
                    isDark ? 'bg-zinc-800 text-zinc-300' : 'bg-white border border-zinc-200 text-zinc-700'
                  }`}
                >
                  模型: {item.model}
                </span>
              </div>
              <span className={`font-mono ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
                {item.createdAt}
              </span>
            </div>

            <div className="text-sm font-semibold text-zinc-100 select-text leading-snug">
              {titleText}
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 pt-1 text-[11px]">
              <span className="text-zinc-400">
                总请求数: <strong className="text-zinc-200 font-mono">{item.requestCount} 次</strong>
              </span>
              <span className="text-zinc-400">
                有效/成功请求: <strong className="text-emerald-400 font-mono">{item.successRequestCount ?? item.requestCount} 次</strong>
              </span>
              {'sessionNum' in item && item.sessionNum && (
                <span className="text-zinc-400">
                  归属会话: <strong className="text-zinc-200 font-mono">#{item.sessionNum}</strong>
                </span>
              )}
              {'ttftMs' in item && item.ttftMs ? (
                <span className="text-zinc-400 flex items-center gap-1">
                  <Clock className="w-3 h-3 text-sky-400" />
                  首字响应 (TTFT): <strong className="text-zinc-200 font-mono">{item.ttftMs}ms</strong>
                </span>
              ) : null}
            </div>
          </div>

          {/* User Prompt (High Priority Feature requested by developers) */}
          <div
            className={`p-3.5 rounded-xl border space-y-2 ${
              isDark ? 'bg-[#161a24] border-zinc-800/90' : 'bg-zinc-50 border-zinc-200'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-zinc-300 flex items-center gap-1.5 text-[11px]">
                <Terminal className="w-3.5 h-3.5 text-sky-400" />
                用户触发该任务的原始 Prompt 指令:
              </span>
              <button
                type="button"
                onClick={handleCopyPrompt}
                className="flex items-center gap-1 px-2 py-0.5 rounded bg-sky-500/15 hover:bg-sky-500/25 text-sky-400 text-[10px] font-medium transition-colors"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? '已复制' : '一键复制'}</span>
              </button>
            </div>
            <div
              className={`p-2.5 rounded-lg font-mono text-[11px] leading-relaxed select-text border ${
                isDark
                  ? 'bg-[#0d1017] border-zinc-800/80 text-zinc-300'
                  : 'bg-white border-zinc-200 text-zinc-700'
              }`}
            >
              {promptText}
            </div>
          </div>

          {/* Token Breakdown & Cache Hit Rate Details (输入/输出/总消耗明确标注) */}
          <div className="grid grid-cols-2 gap-3">
            {/* Cache Hit */}
            <div
              className={`p-3.5 rounded-xl border space-y-1.5 ${
                isDark ? 'bg-[#161a24] border-emerald-500/20' : 'bg-emerald-50/50 border-emerald-200'
              }`}
            >
              <div className="flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1 text-emerald-500 font-medium">
                  <Zap className="w-3.5 h-3.5" />
                  Prompt 缓存命中率
                </span>
                <span className="text-emerald-500 font-mono font-bold text-base">
                  {item.cacheHitRate.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-zinc-700/30 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-400 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(0, item.cacheHitRate))}%` }}
                />
              </div>
              <div className="text-[10px] text-zinc-400 pt-0.5 flex justify-between">
                <span>预估省钱:</span>
                <span className="font-mono text-emerald-400 font-medium">≈ ¥{item.savedCny.toFixed(3)}</span>
              </div>
            </div>

            {/* Total tokens */}
            <div
              className={`p-3.5 rounded-xl border space-y-1.5 ${
                isDark ? 'bg-[#161a24] border-sky-500/20' : 'bg-sky-50/50 border-sky-200'
              }`}
            >
              <div className="flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1 text-sky-400 font-medium">
                  <Coins className="w-3.5 h-3.5" />
                  总 Token 消耗
                </span>
                <span className="text-sky-400 font-mono font-bold text-base">
                  {item.totalTokens} tok
                </span>
              </div>
              <div className="text-[11px] text-zinc-400 flex justify-between font-mono pt-1 border-t border-zinc-700/30">
                <span>输入 Token: <strong className="text-zinc-200">{item.inputTokens}</strong></span>
                <span>输出 Token: <strong className="text-zinc-200">{item.outputTokens}</strong></span>
              </div>
              <div className="text-[10px] text-zinc-400 flex justify-between">
                <span>本次消费预估:</span>
                <span className="font-mono text-amber-400 font-medium">¥{item.costCny.toFixed(3)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div
          className={`flex items-center justify-between px-5 py-3 border-t text-xs ${
            isDark ? 'bg-[#151922] border-zinc-800 text-zinc-400' : 'bg-zinc-50 border-zinc-200 text-zinc-600'
          }`}
        >
          <span>提示：在悬浮胶囊状态下，可通过左右箭头或双击快速展开此任务。</span>
          <button
            type="button"
            onClick={onClose}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors ${
              isDark ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-200' : 'bg-zinc-200 hover:bg-zinc-300 text-zinc-800'
            }`}
          >
            完成查看
          </button>
        </div>
      </div>
    </div>
  );
};
