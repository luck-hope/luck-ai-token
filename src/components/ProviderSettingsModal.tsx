import React, { useState } from 'react';
import { ProviderConfig } from '../types';
import { ProviderIcon } from '../utils/providerBadge';
import {
  X,
  Plus,
  Trash2,
  Save,
  Eye,
  EyeOff,
  Server,
  ShieldCheck,
  Lock,
  FolderOpen,
  RotateCcw,
  Check,
  Copy,
  AlertTriangle,
  HardDrive,
  Globe,
  Sparkles,
} from 'lucide-react';

interface ProviderSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  providers: ProviderConfig[];
  onSaveProviders: (providers: ProviderConfig[]) => void;
  port: number;
  onUpdatePort: (port: number) => void;
  onClearAllSessions?: () => void;
  onResetDefaultSessions?: () => void;
}

export const ProviderSettingsModal: React.FC<ProviderSettingsModalProps> = ({
  isOpen,
  onClose,
  providers,
  onSaveProviders,
  port,
  onUpdatePort,
  onClearAllSessions,
  onResetDefaultSessions,
}) => {
  const [activeTab, setActiveTab] = useState<'providers' | 'storage'>('providers');
  const [providerList, setProviderList] = useState<ProviderConfig[]>(providers);
  const [selectedId, setSelectedId] = useState<string>(providers[0]?.id || '');
  const [showApiKey, setShowApiKey] = useState<boolean>(false);
  const [editPort, setEditPort] = useState<number>(port);

  // 会话存储路径配置
  const [storagePath, setStoragePath] = useState<string>('~/.usage_gateway/sessions/');
  const [copiedPath, setCopiedPath] = useState<boolean>(false);
  const [clearSuccessNotice, setClearSuccessNotice] = useState<string>('');

  if (!isOpen) return null;

  const currentProvider = providerList.find((p) => p.id === selectedId) || providerList[0];
  const isPreset = currentProvider?.isPreset ?? (
    ['prov-openai', 'prov-deepseek', 'prov-sensenova', 'prov-bigmodel', 'openai', 'deepseek', 'sensenova', 'bigmodel'].includes(currentProvider?.id || '') ||
    ['openai', 'deepseek', 'sensenova', 'bigmodel'].includes((currentProvider?.name || '').toLowerCase())
  );

  const handleFieldChange = (field: keyof ProviderConfig, value: string) => {
    setProviderList((prev) =>
      prev.map((p) => (p.id === selectedId ? { ...p, [field]: value } : p))
    );
  };

  // 用户新增自定义服务商（支持手动填写自定义 URL）
  const handleAddNewCustomProvider = () => {
    const newId = `prov-custom-${Date.now()}`;
    const newProv: ProviderConfig = {
      id: newId,
      name: `custom_api_${providerList.length + 1}`,
      type: 'openai-compatible',
      upstreamUrl: 'https://api.your-custom-gateway.com/v1',
      apiKey: '',
      proxy: '',
      modelRoutes: 'custom-*, gpt-*, claude-*',
      isActive: true,
      isPreset: false,
      description: '用户自定义第三方/中转或内网服务商',
    };
    setProviderList([...providerList, newProv]);
    setSelectedId(newId);
  };

  // 删除当前选中的自定义服务商 (预设服务商禁止删除)
  const handleDeleteCurrent = () => {
    if (isPreset) return;
    if (providerList.length <= 1) return;
    const remaining = providerList.filter((p) => p.id !== selectedId);
    setProviderList(remaining);
    setSelectedId(remaining[0].id);
  };

  const handleSaveAndApply = () => {
    onSaveProviders(providerList);
    onUpdatePort(editPort);
    onClose();
  };

  const handleCopyPath = () => {
    navigator.clipboard.writeText(storagePath);
    setCopiedPath(true);
    setTimeout(() => setCopiedPath(false), 2000);
  };

  const handleTriggerClearCache = () => {
    if (onClearAllSessions) {
      onClearAllSessions();
      setClearSuccessNotice('✓ 已成功清理所有本地缓存会话与请求记录');
      setTimeout(() => setClearSuccessNotice(''), 3000);
    }
  };

  const handleTriggerResetSessions = () => {
    if (onResetDefaultSessions) {
      onResetDefaultSessions();
      setClearSuccessNotice('✓ 已恢复默认会话及统计示例数据');
      setTimeout(() => setClearSuccessNotice(''), 3000);
    }
  };

  return (
    <div
      id="provider-settings-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 select-none animate-in fade-in duration-200"
    >
      <div className="w-[560px] max-w-full bg-[#131720] rounded-xl border border-zinc-700/80 shadow-2xl overflow-hidden font-sans text-zinc-200 flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#181c26] border-b border-zinc-800 text-sm font-semibold">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-sky-400" />
            <span>用量网关 · 设置与配置</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1 rounded hover:bg-zinc-700/40 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs: 服务商配置 vs 会话与存储 */}
        <div className="flex items-center gap-2 px-4 pt-2.5 pb-1 bg-[#141720] border-b border-zinc-800/80 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('providers')}
            className={`px-3.5 py-1.5 rounded-t-lg font-bold transition-all flex items-center gap-1.5 ${
              activeTab === 'providers'
                ? 'bg-[#232938] text-sky-300 border-b-2 border-sky-400 shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>服务商配置</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('storage')}
            className={`px-3.5 py-1.5 rounded-t-lg font-bold transition-all flex items-center gap-1.5 ${
              activeTab === 'storage'
                ? 'bg-[#232938] text-sky-300 border-b-2 border-sky-400 shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <HardDrive className="w-3.5 h-3.5" />
            <span>会话与存储</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 space-y-3.5 max-h-[72vh] overflow-y-auto text-xs">
          {activeTab === 'providers' ? (
            <>
              <div className="text-[11px] text-zinc-400 flex items-center justify-between">
                <span>服务商节点 (按模型通配符自动路由转发):</span>
                <span className="flex items-center gap-1 text-emerald-400 font-mono">
                  <ShieldCheck className="w-3 h-3" /> 本地安全隔离
                </span>
              </div>

              {/* 1. 服务商列表 (更新为高清矢量品牌 Icon 与规范状态) */}
              <div className="bg-[#0e1117] rounded-lg border border-zinc-800/90 p-1.5 max-h-40 overflow-y-auto space-y-1 font-sans">
                {providerList.map((p) => {
                  const isSelected = p.id === selectedId;
                  const itemIsPreset = p.isPreset ?? (
                    ['prov-openai', 'prov-deepseek', 'prov-sensenova', 'prov-bigmodel'].includes(p.id) ||
                    ['openai', 'deepseek', 'sensenova', 'bigmodel'].includes(p.name.toLowerCase())
                  );

                  return (
                    <div
                      key={p.id}
                      onClick={() => setSelectedId(p.id)}
                      className={`flex items-center justify-between px-2.5 py-1.5 rounded-md cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-[#21293a] border border-sky-500/50 text-white shadow-xs'
                          : 'hover:bg-[#161b24] text-zinc-400 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        {/* 高清官方矢量 Icon */}
                        <div className="w-6 h-6 rounded flex items-center justify-center bg-zinc-900 border border-zinc-800 flex-shrink-0">
                          <ProviderIcon provider={p.name} size={16} />
                        </div>
                        <span className="font-bold text-zinc-100 font-mono text-xs">{p.name}</span>
                        {itemIsPreset ? (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-sky-950/70 text-sky-400 border border-sky-800/40">
                            预设
                          </span>
                        ) : (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-950/70 text-purple-300 border border-purple-800/40">
                            自定义
                          </span>
                        )}
                        <span className="text-[11px] text-zinc-400 truncate max-w-[190px] font-mono">
                          {p.upstreamUrl}
                        </span>
                      </div>
                      <span className="text-[10px] text-zinc-400 bg-zinc-800/80 px-2 py-0.5 rounded font-mono ml-2 flex-shrink-0 border border-zinc-700/50">
                        {p.modelRoutes.split(',')[0]}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* 2. 当前选中服务商配置表单 */}
              {currentProvider && (
                <div className="space-y-2.5 bg-[#171b24] p-3.5 rounded-lg border border-zinc-800/90">
                  <div className="flex items-center justify-between pb-2 border-b border-zinc-800/70">
                    <div className="flex items-center gap-2">
                      <ProviderIcon provider={currentProvider.name} size={18} />
                      <span className="font-bold text-zinc-100 text-sm">{currentProvider.name}</span>
                      {isPreset ? (
                        <span className="text-[11px] text-sky-400 bg-sky-950/60 px-2 py-0.5 rounded border border-sky-800/50 flex items-center gap-1">
                          <Lock className="w-3 h-3" /> 官方预设服务商 (URL 锁定)
                        </span>
                      ) : (
                        <span className="text-[11px] text-purple-300 bg-purple-950/60 px-2 py-0.5 rounded border border-purple-800/50 flex items-center gap-1">
                          <Sparkles className="w-3 h-3" /> 自定义服务商 (自由填写 URL)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* 名称 */}
                  <div className="grid grid-cols-4 items-center gap-2">
                    <label className="text-zinc-400 text-right pr-1 font-medium">服务商名称</label>
                    <input
                      type="text"
                      value={currentProvider.name}
                      disabled={isPreset}
                      onChange={(e) => handleFieldChange('name', e.target.value)}
                      placeholder="如 deepseek, custom-vllm"
                      className={`col-span-3 border rounded px-2.5 py-1.5 font-mono text-xs focus:outline-hidden ${
                        isPreset
                          ? 'bg-[#0f1218]/70 border-zinc-800 text-zinc-400 cursor-not-allowed'
                          : 'bg-[#0f1218] border-zinc-700/70 text-zinc-100 focus:border-sky-500'
                      }`}
                    />
                  </div>

                  {/* 上游 URL: 预设服务商不提供手动填写 URL，锁定展示；自定义服务商支持完全自由输入 */}
                  <div className="grid grid-cols-4 items-center gap-2">
                    <label className="text-zinc-400 text-right pr-1 font-medium">上游 URL</label>
                    <div className="col-span-3 relative">
                      <input
                        type="text"
                        value={currentProvider.upstreamUrl}
                        disabled={isPreset}
                        onChange={(e) => handleFieldChange('upstreamUrl', e.target.value)}
                        placeholder="填到版本路径为止，如 https://api.openai.com/v1"
                        className={`w-full border rounded px-2.5 py-1.5 font-mono text-xs focus:outline-hidden ${
                          isPreset
                            ? 'bg-[#0c0e14] border-zinc-800/90 text-zinc-400 pr-24 cursor-not-allowed'
                            : 'bg-[#0f1218] border-zinc-700/70 text-zinc-100 focus:border-sky-500'
                        }`}
                      />
                      {isPreset && (
                        <div className="absolute right-2 top-1.5 flex items-center gap-1 text-[10px] text-zinc-400 bg-zinc-800 px-1.5 py-0.5 rounded pointer-events-none">
                          <Lock className="w-3 h-3 text-amber-500" />
                          <span>官方预设节点</span>
                        </div>
                      )}
                    </div>
                  </div>
                  {isPreset && (
                    <div className="grid grid-cols-4 items-center gap-2 -mt-1">
                      <div className="col-span-1" />
                      <div className="col-span-3 text-[10px] text-zinc-500">
                        提示: 预设官方服务商使用固定标准节点以保障稳定统计与路由；如需接入第三方中转请点击「+ 新增自定义服务商」。
                      </div>
                    </div>
                  )}

                  {/* API Key */}
                  <div className="grid grid-cols-4 items-center gap-2">
                    <label className="text-zinc-400 text-right pr-1 font-medium">API Key</label>
                    <div className="col-span-3 relative">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        value={currentProvider.apiKey}
                        onChange={(e) => handleFieldChange('apiKey', e.target.value)}
                        placeholder="填入真实密钥，仅保存在本机内存及本地隔离存储中"
                        className="w-full bg-[#0f1218] border border-zinc-700/70 rounded px-2.5 py-1.5 pr-8 text-zinc-100 focus:border-sky-500 focus:outline-hidden font-mono text-xs"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-2 top-2 text-zinc-400 hover:text-zinc-200"
                        title={showApiKey ? '隐藏密钥' : '显示明文'}
                      >
                        {showApiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {/* 代理 Proxy */}
                  <div className="grid grid-cols-4 items-center gap-2">
                    <label className="text-zinc-400 text-right pr-1 font-medium">网络代理</label>
                    <input
                      type="text"
                      value={currentProvider.proxy || ''}
                      onChange={(e) => handleFieldChange('proxy', e.target.value)}
                      placeholder="可选，如 http://127.0.0.1:7890；留空表示直连"
                      className="col-span-3 bg-[#0f1218] border border-zinc-700/70 rounded px-2.5 py-1.5 text-zinc-100 focus:border-sky-500 focus:outline-hidden font-mono text-xs"
                    />
                  </div>

                  {/* 模型路由通配符 */}
                  <div className="grid grid-cols-4 items-center gap-2">
                    <label className="text-zinc-400 text-right pr-1 font-medium">模型路由</label>
                    <input
                      type="text"
                      value={currentProvider.modelRoutes}
                      onChange={(e) => handleFieldChange('modelRoutes', e.target.value)}
                      placeholder="逗号分隔通配符，如 sensenova-*, deepseek-*, gpt-*"
                      className="col-span-3 bg-[#0f1218] border border-zinc-700/70 rounded px-2.5 py-1.5 text-zinc-100 focus:border-sky-500 focus:outline-hidden font-mono text-xs"
                    />
                  </div>

                  {/* 操作按钮：新增自定义服务商 & 删除 */}
                  <div className="flex items-center justify-between pt-1 border-t border-zinc-800/60 mt-2">
                    <button
                      type="button"
                      onClick={handleAddNewCustomProvider}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/30 font-semibold transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" /> 新增自定义服务商
                    </button>

                    <button
                      type="button"
                      disabled={isPreset}
                      onClick={handleDeleteCurrent}
                      title={isPreset ? '官方预设服务商无法删除' : '删除该自定义服务商'}
                      className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        isPreset
                          ? 'bg-zinc-800/50 text-zinc-600 cursor-not-allowed border border-zinc-800'
                          : 'bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40'
                      }`}
                    >
                      <Trash2 className="w-3.5 h-3.5" /> 删除该服务商
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            /* ── Tab 2: 会话与存储 (原会话与别名规则) ── */
            <div className="space-y-3.5">
              {/* 成功反馈提示 */}
              {clearSuccessNotice && (
                <div className="p-2.5 rounded-lg bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 flex items-center gap-2 font-medium animate-in fade-in">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>{clearSuccessNotice}</span>
                </div>
              )}

              {/* 1. 会话存储默认地址 & 快速打开文件地址 */}
              <div className="p-3.5 rounded-lg bg-[#171b24] border border-zinc-800 space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-zinc-100 flex items-center gap-1.5 text-xs">
                    <FolderOpen className="w-4 h-4 text-amber-400" />
                    <span>用户存储会话的默认地址</span>
                  </div>
                  <span className="text-[10px] text-zinc-400 font-mono">SQLite / JSONL 持久化</span>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={storagePath}
                    onChange={(e) => setStoragePath(e.target.value)}
                    placeholder="输入或自定义存储路径"
                    className="flex-1 bg-[#0f1218] border border-zinc-700/70 rounded px-2.5 py-1.5 text-sky-400 font-mono text-xs focus:border-sky-500 focus:outline-hidden"
                  />
                  <button
                    type="button"
                    onClick={handleCopyPath}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-medium transition-colors flex-shrink-0 border border-zinc-700"
                    title="复制路径并快速在终端或系统资源管理器中打开"
                  >
                    {copiedPath ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400">已复制</span>
                      </>
                    ) : (
                      <>
                        <FolderOpen className="w-3.5 h-3.5 text-amber-400" />
                        <span>快速打开文件地址</span>
                      </>
                    )}
                  </button>
                </div>
                <p className="text-[11px] text-zinc-400 leading-relaxed">
                  所有通过本地网关代理的请求会话、Token 统计、首会话标题及命中率缓存均保存在此目录下。
                </p>
              </div>

              {/* 2. 快速清理所有缓存会话功能 */}
              <div className="p-3.5 rounded-lg bg-[#171b24] border border-zinc-800 space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-zinc-100 flex items-center gap-1.5 text-xs">
                    <RotateCcw className="w-4 h-4 text-rose-400" />
                    <span>会话缓存与数据清理</span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                  <button
                    type="button"
                    onClick={handleTriggerClearCache}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-rose-950/60 hover:bg-rose-900/80 text-rose-200 border border-rose-800/60 font-semibold transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                    <span>快速清理所有缓存会话</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleTriggerResetSessions}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-medium transition-colors border border-zinc-700"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-sky-400" />
                    <span>重置为默认演示会话</span>
                  </button>
                </div>

                <p className="text-[11px] text-zinc-400 leading-relaxed">
                  清理缓存会话后将立即重置内存与本地网关缓存中的历史请求明细，使统计窗口归零。
                </p>
              </div>

              {/* 3. 本地监听端口配置 */}
              <div className="p-3.5 rounded-lg bg-[#171b24] border border-zinc-800 space-y-2">
                <div className="font-bold text-zinc-100 text-xs">本地网关监听端口</div>
                <div className="flex items-center gap-2">
                  <span className="text-zinc-400">当前转发端口:</span>
                  <input
                    type="number"
                    value={editPort}
                    onChange={(e) => setEditPort(Number(e.target.value))}
                    className="w-24 bg-[#0f1218] border border-zinc-700/70 rounded px-2.5 py-1 text-sky-400 font-mono text-xs font-bold"
                  />
                  <span className="text-[11px] text-zinc-400">（修改端口后需重启本地网关服务）</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#10131a] border-t border-zinc-800 text-xs">
          <span className="text-zinc-400 text-[11px]">设置将自动保存并应用于本地代理</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded text-zinc-400 hover:text-white transition-colors"
            >
              取消
            </button>
            <button
              type="button"
              onClick={handleSaveAndApply}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-white font-bold transition-all shadow-[0_0_12px_rgba(2,132,199,0.3)]"
            >
              <Save className="w-3.5 h-3.5" /> 保存并应用
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
