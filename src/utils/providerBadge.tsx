import React from 'react';

export interface ProviderMeta {
  color: string;
  badgeBg: string;
  badgeBorder: string;
  displayName: string;
}

// 1. DeepSeek 蓝鲸鱼 SVG 矢量图标 (100% 对应官方)
export const DeepSeekIcon: React.FC<{ size?: number; className?: string }> = ({ size = 18, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`flex-shrink-0 ${className}`}
  >
    <path
      d="M31 10.5C29 8 26.5 7 23.5 6.8C24.2 5.8 25 4.8 26.2 4.2C26.7 3.9 26.5 3.1 25.8 3.1C23 3.3 20.8 4.8 19.3 6.6C16.2 7 13.2 8.2 10.7 10.3C6.3 13.8 3.8 18.9 3.6 24.5C3.5 26.7 4.2 28.7 5.7 29.9C7.4 31.1 9.6 31.3 12.3 30.7C16.6 29.7 20.4 27.3 23.8 24.2C27 21.3 29.9 17.6 31.2 13.5C31.7 12.3 31.7 11.3 31 10.5ZM21.9 22.2C19 24.8 15.6 26.8 11.8 27.6C9.9 28 8.4 27.9 7.4 27.1C6.6 28.8 8.8 14.6 12.6 11.7C14.7 10.1 17.2 9.1 19.8 8.9C18.6 10.8 18.3 13.2 18.7 15.3C19.2 17.3 20.4 19 21.9 20.2C22.1 20.9 22 21.6 21.9 22.2ZM28.5 12.9C27.3 16.6 24.8 19.7 21.8 22.1C21 20.9 20.4 19.5 20.1 17.9C19.9 16.4 20.1 14.7 20.9 13.3C22.1 11.3 24.1 9.9 26.5 9.4C27.7 10.3 28.3 11.5 28.5 12.9Z"
      fill="#2955fb"
    />
    <circle cx="10.8" cy="17.8" r="1.6" fill="#2955fb" />
  </svg>
);

// 2. OpenAI 经典六瓣螺旋旋涡 SVG 图标
export const OpenAIIcon: React.FC<{ size?: number; className?: string }> = ({ size = 18, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
    className={`flex-shrink-0 text-[#10a37f] dark:text-[#10a37f] ${className}`}
  >
    <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.259 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7466-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.5045 4.5045 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.6667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813l-.0048 6.7227zm1.1448-2.6108l2.553-1.4727a.7854.7854 0 0 1 .7854 0l2.553 1.4727v2.9455l-2.553 1.4727a.7854.7854 0 0 1-.7854 0l-2.553-1.4727z" />
  </svg>
);

// 3. 商汤 TokenPlan (SenseNova) 官方几何四宫格条纹矩阵
export const SenseNovaTokenPlanIcon: React.FC<{ size?: number; className?: string }> = ({ size = 18, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 32 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`flex-shrink-0 ${className}`}
  >
    <defs>
      <pattern id="senseNovaPattern" width="4" height="4" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
        <line x1="0" y1="0" x2="0" y2="4" stroke="#00f5c4" strokeWidth="1.8" />
      </pattern>
    </defs>
    <rect x="2" y="2" width="20" height="20" rx="1.5" fill="#583be8" />
    <rect x="7" y="7" width="15" height="15" fill="url(#senseNovaPattern)" />
    <rect x="12" y="12" width="10" height="10" rx="0.5" fill="#ffffff" />
    <rect x="22" y="12" width="10" height="10" rx="1" fill="#00e5b7" />
    <rect x="12" y="22" width="10" height="10" rx="1" fill="#00e5b7" />
    <rect x="22" y="22" width="10" height="10" rx="1" fill="#4d30df" />
  </svg>
);

// 4. 智谱 GLM 几何立体方块 SVG 图标
export const ZhipuGLMIcon: React.FC<{ size?: number; className?: string }> = ({ size = 18, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 32 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`flex-shrink-0 ${className}`}
  >
    <rect width="32" height="32" rx="7" fill="#3E63DD" />
    <path
      d="M16 7L24 11.6V20.8L16 25.4L8 20.8V11.6L16 7Z"
      stroke="#ffffff"
      strokeWidth="2.2"
      strokeLinejoin="round"
    />
    <path d="M16 16.5V25" stroke="#ffffff" strokeWidth="2.2" />
    <path d="M16 16.5L24 11.8" stroke="#ffffff" strokeWidth="2.2" />
    <path d="M16 16.5L8 11.8" stroke="#ffffff" strokeWidth="2.2" />
  </svg>
);

// 5. Anthropic Claude 暖橙星芒矢量图标
export const AnthropicClaudeIcon: React.FC<{ size?: number; className?: string }> = ({ size = 18, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="#D97757"
    xmlns="http://www.w3.org/2000/svg"
    className={`flex-shrink-0 ${className}`}
  >
    <path d="M17.5 3H14L8 21H11.5L13 16.5H18.5L20 21H23.5L17.5 3ZM14 13.5L15.8 8L17.5 13.5H14ZM4.5 3H1L7 21H10.5L4.5 3Z" />
  </svg>
);

// 6. Google Gemini 四芒星光渐变矢量图标
export const GeminiIcon: React.FC<{ size?: number; className?: string }> = ({ size = 18, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`flex-shrink-0 ${className}`}
  >
    <path
      d="M12 2C12 7.52285 7.52285 12 2 12C7.52285 12 12 16.4772 12 22C12 16.4772 16.4772 12 22 12C16.4772 12 12 7.52285 12 2Z"
      fill="url(#geminiGradient)"
    />
    <defs>
      <linearGradient id="geminiGradient" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
        <stop stopColor="#1BA1E3" />
        <stop offset="0.5" stopColor="#5B7CEF" />
        <stop offset="1" stopColor="#9C66F9" />
      </linearGradient>
    </defs>
  </svg>
);

// 7. 硅基流动 SiliconFlow 图标
export const SiliconFlowIcon: React.FC<{ size?: number; className?: string }> = ({ size = 18, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`flex-shrink-0 ${className}`}
  >
    <rect width="24" height="24" rx="5" fill="#7C3AED" />
    <path
      d="M6 12C6 8.68629 8.68629 6 12 6C15.3137 6 18 8.68629 18 12C18 15.3137 15.3137 18 12 18"
      stroke="#ffffff"
      strokeWidth="2.2"
      strokeLinecap="round"
    />
    <circle cx="12" cy="12" r="2.5" fill="#38BDF8" />
  </svg>
);

// 8. Ollama 标志性骆马/羊驼图标
export const OllamaIcon: React.FC<{ size?: number; className?: string }> = ({ size = 18, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`flex-shrink-0 ${className}`}
  >
    <rect width="24" height="24" rx="5" fill="#18181B" stroke="#3F3F46" strokeWidth="1" />
    <circle cx="12" cy="12" r="5" fill="#FAFAFA" />
    <circle cx="10" cy="11" r="1" fill="#18181B" />
    <circle cx="14" cy="11" r="1" fill="#18181B" />
  </svg>
);

// 9. 自定义/通用服务商图标 (亮蓝齿轮核心)
export const CustomServerIcon: React.FC<{ size?: number; className?: string }> = ({ size = 18, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`flex-shrink-0 ${className}`}
  >
    <rect width="24" height="24" rx="5" fill="#0284C7" />
    <path
      d="M12 8V16M8 12H16M7 7L17 17M17 7L7 17"
      stroke="#ffffff"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
);

export function getProviderMeta(provider: string): ProviderMeta {
  const p = (provider || '').toLowerCase();
  if (p.includes('deepseek')) {
    return {
      color: '#2955fb',
      badgeBg: 'rgba(41, 85, 251, 0.12)',
      badgeBorder: 'rgba(41, 85, 251, 0.35)',
      displayName: 'DeepSeek (深度求索)',
    };
  }
  if (p.includes('sensenova') || p.includes('tokenplan') || p.includes('商汤')) {
    return {
      color: '#583be8',
      badgeBg: 'rgba(88, 59, 232, 0.12)',
      badgeBorder: 'rgba(88, 59, 232, 0.35)',
      displayName: '商汤 SenseNova (日日新)',
    };
  }
  if (p.includes('openai') || p.includes('gpt') || p.includes('o1') || p.includes('o3')) {
    return {
      color: '#10a37f',
      badgeBg: 'rgba(16, 163, 127, 0.12)',
      badgeBorder: 'rgba(16, 163, 127, 0.35)',
      displayName: 'OpenAI 官方',
    };
  }
  if (p.includes('bigmodel') || p.includes('glm') || p.includes('智谱')) {
    return {
      color: '#3E63DD',
      badgeBg: 'rgba(62, 99, 221, 0.12)',
      badgeBorder: 'rgba(62, 99, 221, 0.35)',
      displayName: '智谱 GLM (BigModel)',
    };
  }
  if (p.includes('anthropic') || p.includes('claude')) {
    return {
      color: '#D97757',
      badgeBg: 'rgba(217, 119, 87, 0.12)',
      badgeBorder: 'rgba(217, 119, 87, 0.35)',
      displayName: 'Anthropic Claude',
    };
  }
  if (p.includes('gemini') || p.includes('google')) {
    return {
      color: '#1BA1E3',
      badgeBg: 'rgba(27, 161, 227, 0.12)',
      badgeBorder: 'rgba(27, 161, 227, 0.35)',
      displayName: 'Google Gemini',
    };
  }
  if (p.includes('silicon') || p.includes('硅基')) {
    return {
      color: '#7C3AED',
      badgeBg: 'rgba(124, 58, 237, 0.12)',
      badgeBorder: 'rgba(124, 58, 237, 0.35)',
      displayName: 'SiliconFlow (硅基流动)',
    };
  }
  if (p.includes('ollama') || p.includes('local') || p.includes('本地')) {
    return {
      color: '#71717A',
      badgeBg: 'rgba(113, 113, 122, 0.12)',
      badgeBorder: 'rgba(113, 113, 122, 0.35)',
      displayName: 'Ollama 本地服务',
    };
  }
  return {
    color: '#0284C7',
    badgeBg: 'rgba(2, 132, 199, 0.12)',
    badgeBorder: 'rgba(2, 132, 199, 0.35)',
    displayName: provider || '自定义服务商',
  };
}

export const ProviderIcon: React.FC<{ provider: string; size?: number; className?: string }> = ({
  provider,
  size = 18,
  className = '',
}) => {
  const p = (provider || '').toLowerCase();
  if (p.includes('deepseek')) return <DeepSeekIcon size={size} className={className} />;
  if (p.includes('sensenova') || p.includes('tokenplan') || p.includes('商汤'))
    return <SenseNovaTokenPlanIcon size={size} className={className} />;
  if (p.includes('openai') || p.includes('gpt') || p.includes('o1') || p.includes('o3'))
    return <OpenAIIcon size={size} className={className} />;
  if (p.includes('bigmodel') || p.includes('glm') || p.includes('智谱'))
    return <ZhipuGLMIcon size={size} className={className} />;
  if (p.includes('anthropic') || p.includes('claude'))
    return <AnthropicClaudeIcon size={size} className={className} />;
  if (p.includes('gemini') || p.includes('google'))
    return <GeminiIcon size={size} className={className} />;
  if (p.includes('silicon') || p.includes('硅基'))
    return <SiliconFlowIcon size={size} className={className} />;
  if (p.includes('ollama') || p.includes('local') || p.includes('本地'))
    return <OllamaIcon size={size} className={className} />;
  return <CustomServerIcon size={size} className={className} />;
};

/**
 * 纯高清图标徽标组件，支持 Hover Tooltip
 */
export const ProviderBadge: React.FC<{
  provider: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}> = ({ provider, size = 'md', className = '' }) => {
  const meta = getProviderMeta(provider);
  const px = size === 'sm' ? 16 : size === 'lg' ? 22 : 18;
  const containerClass =
    size === 'sm'
      ? 'w-6 h-6 p-0.5 rounded-md'
      : size === 'lg'
      ? 'w-8 h-8 p-1 rounded-lg'
      : 'w-7 h-7 p-1 rounded-md';

  return (
    <div
      title={`模型服务商: ${meta.displayName} (${provider})`}
      className={`inline-flex items-center justify-center border shadow-2xs cursor-help transition-all duration-150 hover:scale-110 active:scale-95 flex-shrink-0 ${containerClass} ${className}`}
      style={{
        backgroundColor: meta.badgeBg,
        borderColor: meta.badgeBorder,
      }}
    >
      <ProviderIcon provider={provider} size={px} />
    </div>
  );
};
