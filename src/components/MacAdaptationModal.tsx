import React, { useState } from 'react';
import { X, Apple, Copy, Check, ShieldCheck, Terminal, AlertTriangle } from 'lucide-react';

interface MacAdaptationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MacAdaptationModal: React.FC<MacAdaptationModalProps> = ({ isOpen, onClose }) => {
  const [copied, setCopied] = useState<boolean>(false);

  if (!isOpen) return null;

  const macCodeSnippet = `# ========================================================
# macOS 原生无边框悬浮胶囊 & 滚轮兼容代码 (PySide6 / PyQt)
# ========================================================
import sys
import platform
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout

class MacFloatingCapsule(QWidget):
    def __init__(self):
        super().__init__()
        
        # 1. 跨平台无边框与置顶属性 (macOS 特殊处理)
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow
        
        # 在 macOS 上避免 Mission Control 隐藏窗口或 Dock 栏遮挡
        if platform.system() == "Darwin":
            flags |= Qt.WindowType.WindowDoesNotAcceptFocus
            # 兼容 macOS 原生深色/浅色外观切换通知
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
            
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 2. 鼠标拖拽平滑吸附 (避开 macOS 菜单栏高度约 25px 与 Dock 栏)
        self.drag_position = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            # 边界限制：保留 macOS 顶部系统菜单栏 28px 避让区
            if platform.system() == "Darwin":
                new_pos.setY(max(28, new_pos.y()))
            self.move(new_pos)
            event.accept()

    def wheelEvent(self, event):
        # 3. macOS 触摸板/鼠标滚轮高精度浮点 delta 兼容
        # macOS 返回的是高精度像素滚动 pixelDelta()，Windows 返回 angleDelta()
        num_pixels = event.pixelDelta()
        num_degrees = event.angleDelta() / 8
        if not num_pixels.isNull():
            delta_val = num_pixels.y()
        else:
            delta_val = num_degrees.y() / 15
        # 向上/向下翻阅任务
        print(f"[macOS Scroll] delta: {delta_val}")
`;

  const handleCopy = () => {
    navigator.clipboard.writeText(macCodeSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 select-none font-sans">
      <div className="w-[640px] max-w-full bg-[#131722] rounded-2xl border border-zinc-700/80 shadow-2xl overflow-hidden text-zinc-200">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-[#171c28] border-b border-zinc-800 text-sm font-semibold">
          <div className="flex items-center gap-2">
            <Apple className="w-4 h-4 text-sky-400" />
            <span>macOS 平台兼容与跨平台悬浮窗调优说明</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-zinc-700/40 text-zinc-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto text-xs">
          {/* Key Checklist for Mac users */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3 bg-[#181d2a] rounded-xl border border-zinc-800 space-y-1">
              <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
                <ShieldCheck className="w-4 h-4" />
                <span>1. 窗口置顶与 Dock 避让</span>
              </div>
              <p className="text-zinc-400 text-[11px] leading-relaxed">
                在 macOS 上须使用 <code className="text-zinc-200">Qt.SubWindow</code> 配合 <code className="text-zinc-200">WA_MacAlwaysShowToolWindow</code>，防止在切换 Space/全屏工作区时被系统隐藏。
              </p>
            </div>

            <div className="p-3 bg-[#181d2a] rounded-xl border border-zinc-800 space-y-1">
              <div className="flex items-center gap-1.5 font-semibold text-sky-400">
                <Terminal className="w-4 h-4" />
                <span>2. 触摸板像素级平滑滚动</span>
              </div>
              <p className="text-zinc-400 text-[11px] leading-relaxed">
                Mac 触控板生成的是 <code className="text-zinc-200">pixelDelta()</code> 浮点矢量，而非 Windows 的 120 阶跃步进，已在事件分发器中平滑归一化。
              </p>
            </div>
          </div>

          {/* Tkinter vs PySide note */}
          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start gap-2.5 text-amber-200/90 text-[11px]">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong>特别提醒：</strong>如果原 Python 代码使用 Tkinter，Mac 上调用 <code className="text-amber-300">-transparentcolor</code> 会抛出 <code className="text-rose-400">TclError</code>。务必改用 <code className="text-amber-300">-alpha</code> 或直接迁移至 <strong>PySide6 (Qt)</strong> 以获得 100% 完美的亚克力毛玻璃圆角与阴影。
            </div>
          </div>

          {/* Python Code snippet */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-zinc-300">PySide6 macOS 适配片段:</span>
              <button
                type="button"
                onClick={handleCopy}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 font-medium transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? '已复制代码' : '复制 Python 代码'}</span>
              </button>
            </div>

            <pre className="p-3.5 rounded-xl bg-[#0d1017] border border-zinc-800 font-mono text-[11px] text-zinc-300 leading-relaxed overflow-x-auto select-text">
              {macCodeSnippet}
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end px-5 py-3 bg-[#161a26] border-t border-zinc-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs transition-colors"
          >
            知道了，返回原型
          </button>
        </div>
      </div>
    </div>
  );
};
