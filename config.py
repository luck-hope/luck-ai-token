"""
TokenTrackerGateway - 跨平台 AI 用量网关与桌面悬浮窗全局配置
"""
import os

GATEWAY_HOST = os.getenv("GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "4000"))

class UpstreamConfig:
    def __init__(self):
        self.providers = {
            "openai": {
                "name": "OpenAI 官方",
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "api_key": os.getenv("OPENAI_API_KEY", "sk-your-openai-key"),
                "routes": ["gpt-*", "o1*", "o3*"]
            },
            "deepseek": {
                "name": "DeepSeek 深度求索",
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                "api_key": os.getenv("DEEPSEEK_API_KEY", "sk-your-deepseek-key"),
                "routes": ["deepseek-*"]
            },
            "sensenova": {
                "name": "商汤 SenseNova",
                "base_url": os.getenv("SENSENOVA_BASE_URL", "https://api.sensenova.cn/compatible-mode/v1"),
                "api_key": os.getenv("SENSENOVA_API_KEY", "sk-your-sensenova-key"),
                "routes": ["sensenova-*", "nova-*"]
            },
            "bigmodel": {
                "name": "智谱 GLM",
                "base_url": os.getenv("BIGMODEL_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
                "api_key": os.getenv("BIGMODEL_API_KEY", "your-zhipu-key"),
                "routes": ["glm-*", "codegeex-*"]
            }
        }

    def resolve_provider(self, model: str) -> dict:
        m = model.lower()
        if "deepseek" in m:
            return self.providers["deepseek"]
        if "sense" in m or "nova" in m:
            return self.providers["sensenova"]
        if "glm" in m or "zhipu" in m:
            return self.providers["bigmodel"]
        return self.providers["openai"]

UPSTREAM_CONFIG = UpstreamConfig()
