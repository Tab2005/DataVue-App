"""
OpenRouter AI 聚合服務客戶端
基於 openai SDK 連接 OpenRouter API
"""
import os
import httpx
import logging
from typing import Any, Optional, Dict, List, Union, Generator
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """OpenRouter 客戶端 - 對接 OpenAI 相容 API 規範"""

    # 本地備用模型清單
    MODELS = {
        "deepseek/deepseek-v4-flash": {
            "display_name": "DeepSeek V4 Flash",
            "description": "DeepSeek 旗艦 Flash 模型 (預設評估核心)",
            "max_tokens": 8192,
            "provider": "openrouter"
        },
        "deepseek/deepseek-chat": {
            "display_name": "DeepSeek V3",
            "description": "DeepSeek 通用對話模型",
            "max_tokens": 8192,
            "provider": "openrouter"
        },
        "google/gemini-2.5-flash": {
            "display_name": "Gemini 2.5 Flash",
            "description": "Google 輕量高性能模型",
            "max_tokens": 8192,
            "provider": "openrouter"
        },
        "anthropic/claude-3.5-sonnet": {
            "display_name": "Claude 3.5 Sonnet",
            "description": "Anthropic 旗艦推理模型",
            "max_tokens": 8192,
            "provider": "openrouter"
        }
    }

    # 快取模型列表
    _cached_models: Optional[Dict[str, Dict]] = None
    _cache_time: float = 0.0
    CACHE_TTL = 3600.0  # 1 小時快取

    def __init__(self, api_key: Optional[str] = None):
        """初始化 OpenRouter 客戶端"""
        self.api_key = (
            api_key 
            or os.getenv("OPENROUTER_API_KEY") 
            or os.getenv("ZEABUR_AI_HUB_API_KEY")
        )
        if not self.api_key:
            self.client = None
            return

        try:
            clean_key = self.api_key.strip()
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=clean_key,
                default_headers={
                    "HTTP-Referer": "https://datavue-app.zeabur.app",
                    "X-Title": "DataVue-App",
                }
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter Client: {e}")
            self.client = None

        self.model_name = "deepseek/deepseek-v4-flash"

    def fetch_remote_models(self) -> Dict[str, Dict]:
        """從 OpenRouter 伺服器獲取並過濾模型清單"""
        import time
        now = time.time()
        
        # 檢查快取
        if OpenRouterClient._cached_models and (now - OpenRouterClient._cache_time < self.CACHE_TTL):
            return OpenRouterClient._cached_models

        if not self.api_key:
            logger.warning("[OpenRouterClient] No API Key provided, returning fallback models.")
            return self.MODELS

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key.strip()}",
                "HTTP-Referer": "https://datavue-app.zeabur.app",
                "X-Title": "DataVue-App"
            }
            # 發送請求獲取 OpenRouter 模型列表
            with httpx.Client(timeout=10.0) as http_client:
                response = http_client.get("https://openrouter.ai/api/v1/models", headers=headers)
                if response.status_code != 200:
                    logger.error(f"[OpenRouterClient] Failed to fetch models: HTTP {response.status_code}")
                    return self.MODELS
                
                data = response.json()
                raw_models = data.get("data", [])
                
                merged_models = {}
                for m in raw_models:
                    model_id = m.get("id")
                    if not model_id:
                        continue
                        
                    # 過濾主流模型，避免下拉選單有數百個無效或小眾模型
                    lower_id = model_id.lower()
                    is_mainstream = (
                        lower_id.startswith("deepseek/")
                        or lower_id.startswith("anthropic/")
                        or lower_id.startswith("google/")
                        or lower_id.startswith("openai/")
                        or lower_id.startswith("meta/")
                    )
                    if not is_mainstream:
                        continue

                    name = m.get("name") or model_id
                    # 限制顯示字元，美化展示
                    context_length = m.get("context_length", 8192)
                    
                    merged_models[model_id] = {
                        "display_name": name,
                        "description": f"{name} (上下文: {context_length} tokens)",
                        "max_tokens": context_length,
                        "provider": "openrouter"
                    }

                if merged_models:
                    # 快取模型
                    OpenRouterClient._cached_models = merged_models
                    OpenRouterClient._cache_time = now
                    return merged_models
                
                return self.MODELS

        except Exception as e:
            logger.error(f"[OpenRouterClient] Error fetching remote models: {e}")
            return self.MODELS

    def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        user_content: Optional[Union[str, List[Dict[str, Any]]]] = None,
    ) -> str:
        """生成內容 (同步阻塞呼叫)"""
        if not self.client:
            raise RuntimeError("OpenRouter Client not initialized.")

        model_to_use = model or self.model_name
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content if user_content is not None else prompt})

        try:
            # 限制 connect timeout 為 3.0 秒，避免在部署網路不通時卡死 20 秒才 fallback
            api_timeout = (3.0, float(timeout)) if timeout is not None else (3.0, 15.0)
            response = self.client.with_options(timeout=api_timeout).chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or 4096
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"[OpenRouterClient] Generation error: {e}")
            raise

    def generate_content_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """生成內容 (異步串流生成器)"""
        if not self.client:
            raise RuntimeError("OpenRouter Client not initialized.")

        model_to_use = model or self.model_name
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or 4096,
                stream=True
            )
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error(f"[OpenRouterClient] Stream generation error: {e}")
            raise

    def set_model(self, model_name: str):
        self.model_name = model_name

    def get_available_models(self, remote: bool = False) -> Dict[str, Dict]:
        if remote:
            return self.fetch_remote_models()
        return self.MODELS.copy()

    def test_connection(self) -> Dict:
        try:
            response = self.generate_content(prompt="hi", temperature=0, max_tokens=5)
            return {
                "success": True,
                "message": f"Connected! Using {self.model_name}",
                "model": self.model_name
            }
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}", "model": self.model_name}
