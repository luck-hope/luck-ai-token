export type WidgetMode = 'circle' | 'capsule' | 'expanded';
export type ThemeMode = 'dark' | 'light';

export interface RequestRecord {
  id: string;
  requestId: number;
  time: string;
  model: string;
  provider: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  cacheHitTokens: number;
  cacheHitRate: number;
  ttftMs: number; // Time to first token
  durationMs: number;
  costCny: number;
  savedCny: number;
  promptSnippet: string;
  responseSnippet: string;
}

export interface SessionItem {
  id: string;
  sessionNum: number;
  taskCount: number;
  requestCount: number;
  successRequestCount?: number; // 成功/有效请求数
  title: string; // 首会话截断标题
  provider: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  cacheHitRate: number;
  cacheHitTokens: number;
  model: string;
  costCny: number;
  savedCny: number;
  requests: RequestRecord[];
  createdAt: string;
  userPromptSnippet?: string;
}

export interface TaskItem {
  id: string;
  taskNum: number;
  name: string; // 任务/Turn标题
  sessionId: string;
  sessionNum?: number;
  sessionCount?: number;
  requestCount: number; // 请求数
  successRequestCount?: number; // 成功/有效请求数
  provider: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  cacheHitRate: number;
  cacheHitTokens?: number;
  model: string;
  costCny: number;
  savedCny: number;
  createdAt: string;
  userPromptSnippet?: string;
  ttftMs?: number;
  requests?: RequestRecord[];
}

export interface TrackingTarget {
  type: 'turn' | 'session';
  id: string;
  isAuto: boolean; // true: 自动跟踪最新请求; false: 📌 用户手动锁定
}

export interface ColumnVisibility {
  requestCount: boolean; // 请求数 / 有效请求数
  inputTokens: boolean;
  outputTokens: boolean;
  costCny: boolean;
  ttftMs: boolean;
  model: boolean;
}

export interface ProviderConfig {
  id: string;
  name: string;
  type: string;
  upstreamUrl: string;
  apiKey: string;
  proxy?: string;
  modelRoutes: string; // e.g. "sensenova-*, mock-*"
  isActive: boolean;
}
