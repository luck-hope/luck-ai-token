"""
用量与计费统计模块 (gateway/counter.py)
"""
from typing import Dict, Any, List
import time

class UsageTracker:
    def __init__(self):
        self.current_task = {
            "name": "重构流式 usage 提取及悬浮胶囊",
            "model": "o3-mini",
            "provider": "openai",
            "prompt_tokens": 120,
            "completion_tokens": 45,
            "cached_tokens": 99,
            "total_tokens": 165,
            "cache_hit_rate": 82.5,
            "cost_cny": 0.0032,
            "is_streaming": False,
            "request_count": 1,
            "success_request_count": 1,
        }
        self.tasks_history: List[Dict[str, Any]] = [
            {
                "id": "task-5",
                "task_num": 5,
                "name": "OpenAI 思考模型接入与流式 Token 统计",
                "model": "o3-mini",
                "provider": "openai",
                "request_count": 1,
                "success_request_count": 1,
                "input_tokens": 120,
                "output_tokens": 45,
                "cached_tokens": 99,
                "total_tokens": 165,
                "cache_hit_rate": 82.5,
                "cost_cny": 0.0032,
                "created_at": "19:05:12",
            },
            {
                "id": "task-4",
                "task_num": 4,
                "name": "连接池与长连接健康检查优化",
                "model": "deepseek-coder",
                "provider": "deepseek",
                "request_count": 2,
                "success_request_count": 2,
                "input_tokens": 60,
                "output_tokens": 20,
                "cached_tokens": 45,
                "total_tokens": 80,
                "cache_hit_rate": 75.0,
                "cost_cny": 0.0006,
                "created_at": "19:02:40",
            },
            {
                "id": "task-3",
                "task_num": 3,
                "name": "极简悬浮窗置顶与拖拽事件监听",
                "model": "deepseek-coder",
                "provider": "deepseek",
                "request_count": 1,
                "success_request_count": 1,
                "input_tokens": 52,
                "output_tokens": 20,
                "cached_tokens": 35,
                "total_tokens": 72,
                "cache_hit_rate": 68.2,
                "cost_cny": 0.0005,
                "created_at": "18:59:15",
            },
            {
                "id": "task-2",
                "task_num": 2,
                "name": "商汤日日新 TokenPlan 适配与路由",
                "model": "sensenova-v5-5",
                "provider": "sensenova",
                "request_count": 2,
                "success_request_count": 2,
                "input_tokens": 50,
                "output_tokens": 20,
                "cached_tokens": 40,
                "total_tokens": 70,
                "cache_hit_rate": 80.0,
                "cost_cny": 0.0008,
                "created_at": "18:55:00",
            },
            {
                "id": "task-1",
                "task_num": 1,
                "name": "智谱 GLM 多模态路由拦截测试",
                "model": "glm-4-flash",
                "provider": "bigmodel",
                "request_count": 4,
                "success_request_count": 4,
                "input_tokens": 200,
                "output_tokens": 76,
                "cached_tokens": 157,
                "total_tokens": 276,
                "cache_hit_rate": 78.6,
                "cost_cny": 0.0002,
                "created_at": "18:50:30",
            },
        ]
        self.total_requests = 10
        self.total_sessions = 3

    def start_task(self, name: str, model: str):
        self.current_task["name"] = name
        self.current_task["model"] = model
        self.current_task["is_streaming"] = True
        self.total_requests += 1

    def record_usage(self, usage: dict, model: str):
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        
        details = usage.get("prompt_tokens_details", {}) or {}
        cached_tokens = (
            usage.get("prompt_cache_hit_tokens") or
            details.get("cached_tokens") or
            usage.get("cached_tokens") or 0
        )

        hit_rate = (cached_tokens / prompt_tokens * 100.0) if prompt_tokens > 0 else 0.0
        cost_cny = (cached_tokens * 0.5 + (prompt_tokens - cached_tokens) * 2.0 + completion_tokens * 8.0) / 1_000_000

        self.current_task.update({
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cached_tokens": cached_tokens,
            "total_tokens": total_tokens,
            "cache_hit_rate": round(hit_rate, 1),
            "cost_cny": round(cost_cny, 4),
            "is_streaming": False,
            "updated_at": time.time()
        })
        new_history_item = {
            "id": f"task-{len(self.tasks_history)+1}",
            "task_num": len(self.tasks_history)+1,
            "name": self.current_task["name"],
            "model": model,
            "provider": "openai" if "gpt" in model or "o1" in model or "o3" in model else ("deepseek" if "deepseek" in model else ("sensenova" if "nova" in model or "sense" in model else "bigmodel")),
            "request_count": 1,
            "success_request_count": 1,
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "cached_tokens": cached_tokens,
            "total_tokens": total_tokens,
            "cache_hit_rate": round(hit_rate, 1),
            "cost_cny": round(cost_cny, 4),
            "created_at": time.strftime("%H:%M:%S"),
        }
        self.tasks_history.insert(0, new_history_item)

    def get_summary(self):
        return {
            "current": self.current_task,
            "total_requests": self.total_requests,
            "total_sessions": self.total_sessions,
            "tasks": self.tasks_history,
        }
