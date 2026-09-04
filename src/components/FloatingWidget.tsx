import React, { useState, useRef, useEffect } from 'react';
import { WidgetMode, SessionItem, TaskItem, ThemeMode, TrackingTarget } from '../types';
import { MiniOrb } from './MiniOrb';
import { CapsuleBar } from './CapsuleBar';
import { FullGatewayPanel } from './FullGatewayPanel';

interface FloatingWidgetProps {
  mode: WidgetMode;
  onModeChange: (mode: WidgetMode) => void;
  sessions: SessionItem[];
  tasks: TaskItem[];
  port: number;
  totalRequests: number;
  totalSessions: number;
  overallCacheHitRate: number;
  currentSession: SessionItem;
  currentTask: TaskItem;
  isStreaming: boolean;
  onSelectSession: (sess: SessionItem) => void;
  onSelectTask: (task: TaskItem) => void;
  onOpenSettings: () => void;
  isMacStyle?: boolean;
  theme?: ThemeMode;
  onToggleTheme?: () => void;
  trackingTarget?: TrackingTarget;
  onSetTrackingTarget?: (target: TrackingTarget) => void;
  onPrevTask?: () => void;
  onNextTask?: () => void;
  onUnlockTracking?: () => void;
  onTriggerTurn?: () => void;
}

export const FloatingWidget: React.FC<FloatingWidgetProps> = ({
  mode,
  onModeChange,
  sessions,
  tasks,
  port,
  totalRequests,
  totalSessions,
  overallCacheHitRate,
  currentSession,
  currentTask,
  isStreaming,
  onSelectSession,
  onSelectTask,
  onOpenSettings,
  isMacStyle = false,
  theme = 'dark',
  onToggleTheme,
  trackingTarget,
  onSetTrackingTarget,
  onPrevTask,
  onNextTask,
  onUnlockTracking,
  onTriggerTurn,
}) => {
  // Widget position (x, y)
  const [position, setPosition] = useState<{ x: number; y: number }>({ x: 200, y: 70 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [showCostInCapsule, setShowCostInCapsule] = useState<boolean>(false);

  // Panel size: 默认宽 580，高 490，支持全向与上下自由拖拽拉伸
  const [panelSize, setPanelSize] = useState<{ w: number; h: number }>({ w: 580, h: 490 });
  const [isResizing, setIsResizing] = useState<boolean>(false);

  const dragStartRef = useRef<{ mouseX: number; mouseY: number; startX: number; startY: number }>({
    mouseX: 0,
    mouseY: 0,
    startX: 0,
    startY: 0,
  });

  const resizeStartRef = useRef<{
    mouseX: number;
    mouseY: number;
    startW: number;
    startH: number;
    direction: 'both' | 'vertical' | 'horizontal';
  }>({
    mouseX: 0,
    mouseY: 0,
    startW: 0,
    startH: 0,
    direction: 'both',
  });

  // 1. 拖拽逻辑：过滤交互按钮，使用 direct rAF 和 0 延迟跟手
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    const target = e.target as HTMLElement;
    if (
      target.closest('button') ||
      target.closest('input') ||
      target.closest('select') ||
      target.closest('table') ||
      target.closest('.no-drag')
    ) {
      return;
    }

    setIsDragging(true);
    dragStartRef.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      startX: position.x,
      startY: position.y,
    };
    e.preventDefault();
  };

  // 2. 双向 / 纯上下拉伸逻辑
  const handleResizeStart = (e: React.MouseEvent, direction: 'both' | 'vertical' | 'horizontal' = 'both') => {
    e.stopPropagation();
    e.preventDefault();
    setIsResizing(true);
    resizeStartRef.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      startW: panelSize.w,
      startH: panelSize.h,
      direction,
    };
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // 正在拖拽位置 (无 CSS 延迟缓冲，纯粹 1:1 跟手)
      if (isDragging) {
        const dx = e.clientX - dragStartRef.current.mouseX;
        const dy = e.clientY - dragStartRef.current.mouseY;
        const newX = Math.max(10, Math.min(window.innerWidth - 80, dragStartRef.current.startX + dx));
        const newY = Math.max(10, Math.min(window.innerHeight - 60, dragStartRef.current.startY + dy));
        setPosition({ x: newX, y: newY });
      }

      // 正在拉伸尺寸
      if (isResizing) {
        const dx = e.clientX - resizeStartRef.current.mouseX;
        const dy = e.clientY - resizeStartRef.current.mouseY;
        const dir = resizeStartRef.current.direction;

        setPanelSize((prev) => {
          let nextW = prev.w;
          let nextH = prev.h;

          if (dir === 'both' || dir === 'horizontal') {
            nextW = Math.max(480, Math.min(window.innerWidth - position.x - 20, resizeStartRef.current.startW + dx));
          }
          if (dir === 'both' || dir === 'vertical') {
            nextH = Math.max(280, Math.min(window.innerHeight - position.y - 20, resizeStartRef.current.startH + dy));
          }
          return { w: nextW, h: nextH };
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setIsResizing(false);
    };

    if (isDragging || isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, isResizing, position.x, position.y]);

  const displayTitle = currentTask ? currentTask.name : currentSession.title;
  const displayCacheRate = currentTask ? currentTask.cacheHitRate : currentSession.cacheHitRate;
  const displayTokens = currentTask ? currentTask.totalTokens : currentSession.totalTokens;
  const displayCost = currentTask ? currentTask.costCny : currentSession.costCny;
  const displayProvider = currentTask ? currentTask.provider : currentSession.provider;
  const displayRequestCount = currentTask ? currentTask.requestCount : currentSession.requestCount;
  const displaySuccessRequestCount = currentTask
    ? (currentTask.successRequestCount ?? currentTask.requestCount)
    : (currentSession.successRequestCount ?? currentSession.requestCount);

  return (
    <div
      id="draggable-floating-container"
      onMouseDown={handleMouseDown}
      style={{
        transform: `translate3d(${position.x}px, ${position.y}px, 0)`,
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 40,
        // 关键点：拖拽中严格禁用任何 transition，杜绝橡皮筋卡顿粘滞！
        transition: isDragging ? 'none' : 'transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1)',
      }}
      className={`select-none touch-none ${isDragging ? 'cursor-grabbing' : 'cursor-default'}`}
    >
      {/* 1. Circle Mode (Micro Orb) */}
      {mode === 'circle' && (
        <div
          onClick={() => onModeChange('capsule')}
          className="cursor-pointer hover:scale-105 active:scale-95 transition-transform"
          title="单击展开为胶囊条"
        >
          <MiniOrb
            cacheHitRate={displayCacheRate}
            isStreaming={isStreaming}
            size={44}
            showTooltip={true}
          />
        </div>
      )}

      {/* 2. Capsule Mode (Oval Pill Bar) - Focused on current task */}
      {mode === 'capsule' && (
        <CapsuleBar
          sessionTitle={displayTitle}
          cacheHitRate={displayCacheRate}
          totalTokens={displayTokens}
          costCny={displayCost}
          requestCount={displayRequestCount}
          successRequestCount={displaySuccessRequestCount}
          provider={displayProvider}
          isStreaming={isStreaming}
          showCost={showCostInCapsule}
          onToggleCostType={() => setShowCostInCapsule(!showCostInCapsule)}
          onExpand={() => onModeChange('expanded')}
          onShrinkToCircle={() => onModeChange('circle')}
          isMacStyle={isMacStyle}
          theme={theme}
          onToggleTheme={onToggleTheme}
          trackingTarget={trackingTarget}
          onPrevTask={onPrevTask}
          onNextTask={onNextTask}
          onUnlockTracking={onUnlockTracking}
        />
      )}

      {/* 3. Expanded Full Window Mode - 支持上下左右自由拉伸 */}
      {mode === 'expanded' && (
        <div className="relative group/panel">
          <FullGatewayPanel
            sessions={sessions}
            tasks={tasks}
            port={port}
            totalRequests={totalRequests}
            totalSessions={totalSessions}
            overallCacheHitRate={overallCacheHitRate}
            selectedSession={currentSession}
            onSelectSession={onSelectSession}
            onSelectTask={onSelectTask}
            onCloseToCapsule={() => onModeChange('capsule')}
            onCloseToCircle={() => onModeChange('circle')}
            onOpenSettings={onOpenSettings}
            isMacStyle={isMacStyle}
            theme={theme}
            onToggleTheme={onToggleTheme}
            trackingTarget={trackingTarget}
            onSetTrackingTarget={onSetTrackingTarget}
            customWidth={panelSize.w}
            customHeight={panelSize.h}
            onTriggerTurn={onTriggerTurn}
            isStreaming={isStreaming}
          />

          {/* ── 底部上下拉伸控制器 (纯隐形响应区域，移除任何突兀的蓝色背景或高亮) ── */}
          <div
            onMouseDown={(e) => handleResizeStart(e, 'vertical')}
            className="absolute -bottom-1.5 left-2 right-2 h-3 cursor-ns-resize z-50"
          />

          {/* ── 右侧左右拉伸控制器 (纯隐形响应区域，保持界面纯净原生) ── */}
          <div
            onMouseDown={(e) => handleResizeStart(e, 'horizontal')}
            className="absolute top-2 bottom-2 -right-1.5 w-3 cursor-ew-resize z-50"
          />

          {/* ── 右下角双向自由拉伸手柄 (纯隐形区域，不显示任何蓝色角标或图标) ── */}
          <div
            onMouseDown={(e) => handleResizeStart(e, 'both')}
            className="absolute -bottom-1.5 -right-1.5 w-5 h-5 cursor-nwse-resize z-50"
          />
        </div>
      )}
    </div>
  );
};
