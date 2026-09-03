import React from 'react';

interface MiniOrbProps {
  cacheHitRate: number; // e.g. 76.7
  isStreaming?: boolean;
  size?: number; // default 40
  onClick?: () => void;
  className?: string;
  showTooltip?: boolean;
}

export const MiniOrb: React.FC<MiniOrbProps> = ({
  cacheHitRate,
  isStreaming = false,
  size = 42,
  onClick,
  className = '',
  showTooltip = true,
}) => {
  // SVG circular arc calculation
  // Radius and circumference
  const strokeWidth = 3.5;
  const radius = (size - strokeWidth * 2 - 4) / 2;
  const circumference = 2 * Math.PI * radius;
  // Arc length proportional to hit rate (0 ~ 100)
  const normalizedRate = Math.min(100, Math.max(0, cacheHitRate));
  const strokeDashoffset = circumference - (normalizedRate / 100) * circumference;

  return (
    <div
      id="gateway-mini-orb"
      onClick={onClick}
      title={showTooltip ? `缓存命中率: ${cacheHitRate.toFixed(1)}% | 点击切换展开` : undefined}
      className={`group relative flex items-center justify-center cursor-pointer select-none transition-transform duration-200 active:scale-95 ${className}`}
      style={{ width: size, height: size }}
    >
      {/* Outer subtle neutral border (clean, no jarring blue glow) */}
      <div className="absolute inset-0 rounded-full border border-white/10 bg-[#11141a] shadow-md" />

      {/* Rotating / Pulsing SVG gauge */}
      <svg
        className="w-full h-full -rotate-90 transform z-10"
        viewBox={`0 0 ${size} ${size}`}
      >
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#1e232d"
          strokeWidth={strokeWidth}
        />
        {/* Active Cache Hit Green Arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#4ade80" // Vibrant green matching image
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-500 ease-out"
        />
      </svg>

      {/* Center glowing blue core dot */}
      <div className="absolute z-20 flex items-center justify-center">
        <div
          className={`rounded-full bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.9)] transition-all ${
            isStreaming ? 'w-2.5 h-2.5 animate-ping opacity-75' : 'w-2 h-2'
          }`}
        />
        <div className="absolute w-2 h-2 rounded-full bg-sky-300" />
      </div>

      {/* Streaming pulse ring effect */}
      {isStreaming && (
        <span className="absolute -inset-1 rounded-full border border-emerald-400/60 animate-ping pointer-events-none" />
      )}
    </div>
  );
};
