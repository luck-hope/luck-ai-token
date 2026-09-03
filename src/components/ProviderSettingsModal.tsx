import React, { useState } from 'react';
import { ProviderConfig } from '../types';
import { X, Plus, Trash2, Save, Eye, EyeOff, Server, ShieldCheck } from 'lucide-react';

interface ProviderSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  providers: ProviderConfig[];
  onSaveProviders: (providers: ProviderConfig[]) => void;
  port: number;
  onUpdatePort: (port: number) => void;
}

export const ProviderSettingsModal: React.FC<ProviderSettingsModalProps> = ({
  isOpen,
  onClose,
  providers,
  onSaveProviders,
  port,
  onUpdatePort,
}) => {
  const [activeTab, setActiveTab] = useState<'providers' | 'sessions'>('providers');
  const [providerList, setProviderList] = useState<ProviderConfig[]>(providers);
  const [selectedId, setSelectedId] = useState<string>(providers[0]?.id || '');
  const [showApiKey, setShowApiKey] = useState<boolean>(false);
  const [editPort, setEditPort] = useState<number>(port);

  if (!isOpen) return null;

  const currentProvider = providerList.find((p) => p.id === selectedId) || providerList[0];

  const handleFieldChange = (field: keyof ProviderConfig, value: string) => {
    setProviderList((prev) =>
      prev.map((p) => (p.id === selectedId ? { ...p, [field]: value } : p))
    );
  };

  const handleAddNew = () => {
    const newId = `prov-${Date.now()}`;
    const newProv: ProviderConfig = {
      id: newId,
      name: 'new_provider',
      type: 'openai',
      upstreamUrl: 'https://api.example.com/v1',
      apiKey: '',
      proxy: '',
      modelRoutes: 'gpt-*, claude-*',
      isActive: true,
    };
    setProviderList([...providerList, newProv]);
    setSelectedId(newId);
  };

  const handleDeleteCurrent = () => {
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

  const getProviderBadge = (name: string) => {
    const firstChar = name.charAt(0).toUpperCase();
    if (name.includes('mock')) return { char: 'M', bg: 'bg-zinc-600' };
    if (name.includes('bigmodel')) return { char: '智', bg: 'bg-blue-600' };
    if (name.includes('sensenova')) return { char: '商', bg: 'bg-rose-600' };
    if (name.includes('deepseek')) return { char: 'D', bg: 'bg-indigo-600' };
    return { char: firstChar, bg: 'bg-sky-600' };
  };

  return (
    <div
      id="provider-settings-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 select-none"
    >
      <div className="w-[520px] max-w-full bg-[#131720] rounded-xl border border-zinc-700/80 shadow-2xl overflow-hidden font-sans text-zinc-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#181c26] border-b border-zinc-800 text-sm font-semibold">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-sky-400" />
            <span>用量网关 · 设置</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1 rounded hover:bg-zinc-700/40 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-2 px-4 pt-2.5 pb-1 bg-[#141720] border-b border-zinc-800/80 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('providers')}
            className={`px-3 py-1.5 rounded font-medium transition-colors ${
              activeTab === 'providers'
                ? 'bg-[#232938] text-sky-300 border-b-2 border-sky-400'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            服务商配置
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('sessions')}
            className={`px-3 py-1.5 rounded font-medium transition-colors ${
              activeTab === 'sessions'
                ? 'bg-[#232938] text-sky-300 border-b-2 border-sky-400'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            会话与别名规则
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 space-y-3.5 max-h-[75vh] overflow-y-auto text-xs">
          {activeTab === 'providers' ? (
            <>
              <div className="text-[11px] text-zinc-400 flex items-center justify-between">
                <span>服务商 (按模型通配符路由, API Key 只保存在本机):</span>
                <span className="flex items-center gap-1 text-emerald-400 font-mono">
                  <ShieldCheck className="w-3 h-3" /> 本地隔离存储
                </span>
              </div>

              {/* Provider List Pills */}
              <div className="bg-[#0e1117] rounded-lg border border-zinc-800 p-1.5 max-h-36 overflow-y-auto space-y-1 font-mono">
                {providerList.map((p) => {
                  const badge = getProviderBadge(p.name);
                  const isSelected = p.id === selectedId;
                  return (
                    <div
                      key={p.id}
                      onClick={() => setSelectedId(p.id)}
                      className={`flex items-center justify-between px-2 py-1.5 rounded cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-[#21293a] border border-sky-500/40 text-white'
                          : 'hover:bg-[#161b24] text-zinc-400'
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span
                          className={`w-4 h-4 rounded-full ${badge.bg} text-[10px] text-white flex items-center justify-center font-bold`}
                        >
                          {badge.char}
                        </span>
                        <span className="font-semibold text-zinc-200">{p.name}</span>
                        <span className="text-[10px] text-zinc-500">[{p.type}]</span>
                        <span className="text-[11px] text-zinc-400 truncate max-w-[200px]">
                          {p.upstreamUrl}
                        </span>
                      </div>
                      <span className="text-[10px] text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded ml-2 flex-shrink-0">
                        {p.modelRoutes.split(',')[0]}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Edit Current Provider Form */}
              {currentProvider && (
                <div className="space-y-2 bg-[#171b24] p-3 rounded-lg border border-zinc-800/80">
                  <div className="grid grid-cols-4 items-center gap-2">
                    <label className="text-zinc-400 text-right pr-1">名称</label>
                    <input
                      type="text"
                      value={currentProvider.name}
                      onChange={(e) => handleFieldChange('name', e.target.value)}
                      placeholder="如 sensenova"
                      className="col-span-3 bg-[#0f1218] border border-zinc-700/60 rounded px-2.5 py-1 text-zinc-200 focus:border-sky-500 focus:outline-hidden font-mono"
                    />
                  </div>

                  <div className="grid grid-cols-4 items-center gap-2">
                    <label className="text-zinc-400 text-right pr-1">上游 URL</label>
                    <input
                      type="text"
                      value={currentProvider.upstreamUrl}
                      onChange={(e) => handleFieldChange('upstreamUrl', e.target.value)}
                      placeholder="填到版本路径为止,如 https://token.../v1"
                      className="col-span-3 bg-[#0f1218] border border-zinc-700/60 rounded px-2.5 py-1 text-zinc-200 focus:border-sky-500 focus:outline-hidden font-mono"
                    />
                  </div>

                  <div className="grid grid-cols-4 items-center gap-2">
                    <label className="text-zinc-400 text-right pr-1">API Key</label>
                    <div className="col-span-3 relative">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        value={currentProvider.apiKey}
                        onChange={(e) => handleFieldChange('apiKey', e.target.value)}
                        placeholder="真实密钥,只保存在本机"
                        className="w-full bg-[#0f1218] border border-zinc-700/60 rounded px-2.5 py-1 pr-8 text-zinc-200 focus:border-sky-500 focus:outline-hidden font-mono"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-2 top-1.5 text-zinc-500 hover:text-zinc-300"
                      >
                        {showApiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-4 items-center gap-2">
                    <label className="text-zinc-400 text-right pr-1">代理</label>
                    <input
                      type="text"
                      value={currentProvider.proxy || ''}
                      onChange={(e) => handleFieldChange('proxy', e.target.value)}
                      placeholder="可选,如 http://127.0.0.1:7890;留空直连"
                      className="col-span-3 bg-[#0f1218] border border-zinc-700/60 rounded px-2.5 py-1 text-zinc-200 focus:border-sky-500 focus:outline-hidden font-mono"
                    />
                  </div>

                  <div className="grid grid-cols-4 items-center gap-2">
                    <label className="text-zinc-400 text-right pr-1">模型路由</label>
                    <input
                      type="text"
                      value={currentProvider.modelRoutes}
                      onChange={(e) => handleFieldChange('modelRoutes', e.target.value)}
                      placeholder="逗号分隔通配符,如 sensenova-*, mock-*"
                      className="col-span-3 bg-[#0f1218] border border-zinc-700/60 rounded px-2.5 py-1 text-zinc-200 focus:border-sky-500 focus:outline-hidden font-mono"
                    />
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleAddNew}
                        className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#232938] hover:bg-[#2c3447] text-sky-300 font-medium transition-colors"
                      >
                        <Plus className="w-3.5 h-3.5" /> 新建
                      </button>
                      <button
                        type="button"
                        onClick={handleDeleteCurrent}
                        className="flex items-center gap-1 px-2.5 py-1 rounded bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" /> 删除选中
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Tab 2: Sessions & Alias mapping */
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-[#171b24] border border-zinc-800 space-y-2">
                <div className="font-semibold text-zinc-200">首会话标题自动截断规则</div>
                <p className="text-zinc-400 text-[11px] leading-relaxed">
                  网关拦截每轮首条 User Message，提取前 16~24 字符作为轻量椭圆胶囊的显示标题。
                  已支持去除常用 Markdown 标题符 (#, ```) 与系统 Prompt 前缀。
                </p>
              </div>

              <div className="p-3 rounded-lg bg-[#171b24] border border-zinc-800 space-y-2">
                <div className="font-semibold text-zinc-200">本地监听端口配置</div>
                <div className="flex items-center gap-2">
                  <span className="text-zinc-400">当前端口:</span>
                  <input
                    type="number"
                    value={editPort}
                    onChange={(e) => setEditPort(Number(e.target.value))}
                    className="w-24 bg-[#0f1218] border border-zinc-700/60 rounded px-2 py-1 text-sky-400 font-mono text-xs"
                  />
                  <span className="text-[10px] text-zinc-500">（修改端口需重启本地 Python 脚本）</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#10131a] border-t border-zinc-800 text-xs">
          <span className="text-zinc-500 text-[11px]">改端口需重启程序</span>
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
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-medium transition-colors shadow-[0_0_12px_rgba(16,185,129,0.3)]"
            >
              <Save className="w-3.5 h-3.5" /> 保存并应用
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
