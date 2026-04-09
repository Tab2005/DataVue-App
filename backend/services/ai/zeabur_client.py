"""
Zeabur AI Hub 統一客戶端
使用 OpenAI 相容 API 支援多種 AI 模型: Gemini, Claude, GPT 等
"""
from openai import OpenAI
from typing import Generator, Optional, Dict, Iterator, Union
import logging
import os

logger = logging.getLogger(__name__)


class ZeaburAIClient:
    """Zeabur AI Hub 客戶端 - 透過 OpenAI 相容 API 統一調用多種 AI 模型"""

    # 支援的模型列表與配置 (作為本地備份與顯示說明)
    MODELS = {
        # Gemini 模型 (推薦 - 免費額度高)
        "gemini-2.0-flash": {
            "provider": "gemini",
            "max_tokens": 8192,
            "description": "Gemini 2.0 Flash (最新世代、極速) ✅ 推薦",
            "description_en": "Gemini 2.0 Flash (Latest, Fast) ✅ Recommended"
        },
        "gemini-1.5-flash": {
            "provider": "gemini",
            "max_tokens": 8192,
            "description": "Gemini 1.5 Flash (經典、高穩定性)",
            "description_en": "Gemini 1.5 Flash (Stable)"
        },
        "gemini-1.5-pro": {
            "provider": "gemini",
            "max_tokens": 32000,
            "description": "Gemini 1.5 Pro (高品質、長文本)",
            "description_en": "Gemini 1.5 Pro (High Quality, Long Context)"
        },

        # Claude 模型
        "claude-3-5-sonnet": {
            "provider": "anthropic",
            "max_tokens": 8192,
            "description": "Claude 3.5 Sonnet (最強智慧品質)",
            "description_en": "Claude 3.5 Sonnet (Intelligent)"
        },
        "claude-3-5-haiku": {
            "provider": "anthropic",
            "max_tokens": 8192,
            "description": "Claude 3.5 Haiku (極速回應)",
            "description_en": "Claude 3.5 Haiku (Fast)"
        },

        # GPT 模型
        "gpt-4o": {
            "provider": "openai",
            "max_tokens": 16000,
            "description": "GPT-4o (OpenAI 旗艦模型)",
            "description_en": "GPT-4o (Flagship)"
        },
        "gpt-4o-mini": {
            "provider": "openai",
            "max_tokens": 16000,
            "description": "GPT-4o Mini (高效能迷你)",
            "description_en": "GPT-4o Mini (Efficient)"
        },

        # 其他模型
        "deepseek-v3": {
            "provider": "deepseek",
            "max_tokens": 8192,
            "description": "DeepSeek V3 (強大推理)",
            "description_en": "DeepSeek V3 (Reasoning)"
        },
        "qwen-2.5-72b": {
            "provider": "qwen",
            "max_tokens": 8192,
            "description": "Qwen 2.5 (通義千問，中文優化)",
            "description_en": "Qwen 2.5 (Chinese Optimized)"
        }
    }

    # Zeabur AI Hub 端點
    ENDPOINTS = {
        "tokyo": "https://hnd1.aihub.zeabur.ai/v1",
        "sanfrancisco": "https://sfo1.aihub.zeabur.ai/v1"
    }

    def __init__(
        self, 
        api_key: Optional[str] = None,
        endpoint: str = "tokyo"
    ):
        """
        初始化 Zeabur AI Hub 客戶端

        Args:
            api_key: Zeabur AI Hub API Key (格式: sk-xxxxxxxx)
                    如未提供，從環境變數 ZEABUR_AI_HUB_API_KEY 讀取
            endpoint: API 端點名稱
                     - "tokyo" (東京，推薦亞洲用戶)
                     - "sanfrancisco" (舊金山)
        """
        self.api_key = api_key or os.getenv("ZEABUR_AI_HUB_API_KEY")
        if not self.api_key:
            self.client = None
            self.base_url = self.ENDPOINTS.get(endpoint, endpoint)
            return

        # 選擇端點
        if endpoint in self.ENDPOINTS:
            self.base_url = self.ENDPOINTS[endpoint]
        else:
            # 允許直接傳入完整 URL
            self.base_url = endpoint.rstrip('/') + '/v1' if not endpoint.endswith('/v1') else endpoint

        # 建立 OpenAI 相容客戶端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        logger.info("Zeabur AI Client initialized with endpoint: %s", self.base_url)

    def fetch_remote_models(self) -> Dict[str, Dict]:
        """
        從 Zeabur 伺服器同步最新可用模型清單

        Returns:
            Dict: 模型清單與說明
        """
        if not self.client:
            return self.MODELS

        try:
            remote_models = self.client.models.list()
            merged_models = {}
            
            for m in remote_models.data:
                model_id = m.id
                
                # 如果是我們已知的模型，沿用豐富的說明
                if model_id in self.MODELS:
                    merged_models[model_id] = self.MODELS[model_id]
                else:
                    # 如果是未知模型，智慧判斷 Provider
                    provider = "unknown"
                    if "gemini" in model_id: provider = "gemini"
                    elif "claude" in model_id: provider = "anthropic"
                    elif "gpt" in model_id: provider = "openai"
                    elif "deepseek" in model_id: provider = "deepseek"
                    elif "qwen" in model_id: provider = "qwen"
                    elif "llama" in model_id: provider = "meta"

                    merged_models[model_id] = {
                        "provider": provider,
                        "max_tokens": 8192,
                        "description": f"{model_id} (外部同步)",
                        "description_en": f"{model_id} (Synced)"
                    }
            
            # 若同步結果為空，回退至本地預設
            return merged_models if merged_models else self.MODELS
        except Exception as e:
            logger.error("Failed to fetch remote models: %s", e)
            return self.MODELS

    def generate_content(
        self,
        prompt: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        system_prompt: Optional[str] = None
    ) -> Union[str, Iterator[str]]:
        """
        生成 AI 內容
        """
        if not self.client:
             raise RuntimeError("AI Client not initialized. API Key is missing.")

        if not model:
            raise ValueError("Model name is required")

        # 嘗試從 MODELS 獲取配置，否則使用預設值
        model_config = self.MODELS.get(model, {"max_tokens": 8192, "provider": "unknown"})
        max_output = max_tokens or model_config["max_tokens"]

        # 構建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        logger.debug("Generating content with %s", model)

        try:
            if stream:
                # 串流模式
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_output,
                    stream=True
                )

                def stream_generator():
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content

                return stream_generator()
            else:
                # 一次性返回
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_output
                )

                return response.choices[0].message.content

        except Exception as e:
            logger.error("AI generation failed: %s", e, exc_info=True)
            raise

    def get_available_models(self, remote: bool = False) -> Dict[str, Dict]:
        """
        獲取可用模型列表
        """
        if remote:
            return self.fetch_remote_models()
        return self.MODELS.copy()

    def get_model_info(self, model: str) -> Dict:
        """
        獲取特定模型資訊
        """
        if model in self.MODELS:
            return self.MODELS[model].copy()
        return {"provider": "unknown", "max_tokens": 8192, "description": model}

    def test_connection(self, model: str = "gemini-1.5-flash") -> bool:
        """
        測試 AI 服務連線
        """
        try:
            self.generate_content(
                prompt="Hello",
                model=model,
                max_tokens=10,
                stream=False
            )
            return True
        except Exception as e:
            logger.error("Connection test failed: %s", e, exc_info=True)
            return False


# 測試用函數
def test_client():
    """
    測試 Zeabur AI Client
    """
    print("=== Testing Zeabur AI Client ===\n")
    try:
        client = ZeaburAIClient()
        print("Test 1: Available models")
        print("-" * 50)
        models = client.get_available_models()
        for model_name, config in models.items():
            print(f"- {model_name}: {config['description']}")
        print("\n=== All tests passed! ===")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")

if __name__ == "__main__":
    test_client()
