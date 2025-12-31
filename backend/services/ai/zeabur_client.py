"""
Zeabur AI Hub 統一客戶端
使用 OpenAI 相容 API 支援多種 AI 模型: Gemini, Claude, GPT 等
"""
from openai import OpenAI
from typing import Generator, Optional, Dict, Iterator
import os


class ZeaburAIClient:
    """Zeabur AI Hub 客戶端 - 透過 OpenAI 相容 API 統一調用多種 AI 模型"""

    # 支援的模型列表與配置
    MODELS = {
        # Gemini 模型 (推薦 - 免費額度高)
        "gemini-2.5-flash": {
            "provider": "gemini",
            "max_tokens": 8192,
            "description": "Gemini 2.5 Flash (快速、免費額度高) ✅ 推薦",
            "description_en": "Gemini 2.5 Flash (Fast, High Free Quota) ✅ Recommended"
        },
        "gemini-2.5-pro": {
            "provider": "gemini",
            "max_tokens": 32000,
            "description": "Gemini 2.5 Pro (高品質、長文本)",
            "description_en": "Gemini 2.5 Pro (High Quality, Long Context)"
        },
        "gemini-3-flash-preview": {
            "provider": "gemini",
            "max_tokens": 8192,
            "description": "Gemini 3.0 Flash Preview (最新預覽)",
            "description_en": "Gemini 3.0 Flash Preview (Latest)"
        },

        # Claude 模型
        "claude-sonnet-4-5": {
            "provider": "anthropic",
            "max_tokens": 8192,
            "description": "Claude 4.5 Sonnet (Anthropic 高品質)",
            "description_en": "Claude 4.5 Sonnet (High Quality)"
        },
        "claude-haiku-4-5": {
            "provider": "anthropic",
            "max_tokens": 8192,
            "description": "Claude 4.5 Haiku (快速、經濟)",
            "description_en": "Claude 4.5 Haiku (Fast, Economical)"
        },

        # GPT 模型
        "gpt-4o": {
            "provider": "openai",
            "max_tokens": 16000,
            "description": "GPT-4o (多模態)",
            "description_en": "GPT-4o (Multimodal)"
        },
        "gpt-4o-mini": {
            "provider": "openai",
            "max_tokens": 16000,
            "description": "GPT-4o Mini (經濟實惠)",
            "description_en": "GPT-4o Mini (Economical)"
        },

        # 其他模型
        "deepseek-v3.2": {
            "provider": "deepseek",
            "max_tokens": 8192,
            "description": "DeepSeek V3.2 (開源高品質)",
            "description_en": "DeepSeek V3.2 (Open Source)"
        },
        "qwen-3-32": {
            "provider": "qwen",
            "max_tokens": 8192,
            "description": "Qwen 3-32B (通義千問，中文優化)",
            "description_en": "Qwen 3-32B (Chinese Optimized)"
        },
        "llama-3.3-70b": {
            "provider": "meta",
            "max_tokens": 8192,
            "description": "Llama 3.3 70B (Meta 開源)",
            "description_en": "Llama 3.3 70B (Meta Open Source)"
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
            raise RuntimeError(
                "ZEABUR_AI_HUB_API_KEY is required. "
                "Please set it in environment or pass as parameter."
            )

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
        print(f"[INFO] Zeabur AI Client initialized with endpoint: {self.base_url}")

    def generate_content(
        self,
        prompt: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        system_prompt: Optional[str] = None
    ) -> str | Iterator[str]:
        """
        生成 AI 內容

        Args:
            prompt: 提示詞
            model: 模型名稱（見 MODELS 字典）
            temperature: 創意度 (0.0-1.0)
                        - 0.0-0.3: 更確定、一致
                        - 0.4-0.7: 平衡（推薦）
                        - 0.8-1.0: 更創意、多樣
            max_tokens: 最大輸出 token 數（None 則使用模型預設值）
            stream: 是否串流輸出
            system_prompt: 系統提示詞（可選）

        Returns:
            生成的文本（字串）或串流 Iterator

        Raises:
            ValueError: 不支援的模型
            Exception: API 調用失敗
        """
        # 驗證模型
        if model not in self.MODELS:
            available = ", ".join(self.MODELS.keys())
            raise ValueError(
                f"Unsupported model: {model}\n"
                f"Available models: {available}"
            )

        model_config = self.MODELS[model]
        max_output = max_tokens or model_config["max_tokens"]

        # 構建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        print(f"[INFO] Generating content with {model} (provider: {model_config['provider']})")
        print(f"[INFO] Temperature: {temperature}, Max tokens: {max_output}")

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
            print(f"[ERROR] AI generation failed: {e}")
            raise

    def get_available_models(self) -> Dict[str, Dict]:
        """
        獲取可用模型列表

        Returns:
            模型配置字典
        """
        return self.MODELS.copy()

    def get_model_info(self, model: str) -> Dict:
        """
        獲取特定模型資訊

        Args:
            model: 模型名稱

        Returns:
            模型配置資訊
        """
        if model not in self.MODELS:
            raise ValueError(f"Unknown model: {model}")

        return self.MODELS[model].copy()

    def test_connection(self, model: str = "gemini-2.5-flash") -> bool:
        """
        測試 AI 服務連線

        Args:
            model: 用於測試的模型

        Returns:
            True if connection successful
        """
        try:
            response = self.generate_content(
                prompt="Hello",
                model=model,
                max_tokens=10,
                stream=False
            )
            return True
        except Exception as e:
            print(f"[ERROR] Connection test failed: {e}")
            return False


# 測試用函數
def test_client():
    """
    測試 Zeabur AI Client
    使用前請先設定環境變數: ZEABUR_AI_HUB_API_KEY
    """
    print("=== Testing Zeabur AI Client ===\n")

    try:
        # 初始化客戶端
        client = ZeaburAIClient()

        # 測試簡單生成
        print("Test 1: Simple generation with Gemini 2.5 Flash")
        print("-" * 50)

        prompt = "用一句話介紹 Facebook 廣告優化"
        response = client.generate_content(
            prompt=prompt,
            model="gemini-2.5-flash",
            temperature=0.7
        )

        print(f"Prompt: {prompt}")
        print(f"Response: {response}\n")

        # 列出可用模型
        print("Test 2: Available models")
        print("-" * 50)
        models = client.get_available_models()
        for model_name, config in models.items():
            print(f"- {model_name}: {config['description']}")

        print("\n=== All tests passed! ===")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_client()
