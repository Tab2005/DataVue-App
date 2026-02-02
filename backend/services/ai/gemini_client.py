"""
Google Gemini 直連客戶端
直接使用 Google AI Studio 的 API Key 呼叫 Gemini 模型
"""
import google.genai as genai
from typing import Optional, Dict, List
import os


class GoogleGeminiClient:
    """Google Gemini 直連客戶端 - 使用 Google AI Studio API Key"""

    # 支援的 Gemini 模型
    MODELS = {
        "gemini-2.5-flash": {
            "display_name": "Gemini 2.5 Flash",
            "description": "快速、免費額度高 ✅ 推薦",
            "max_tokens": 8192
        },
        "gemini-2.5-pro": {
            "display_name": "Gemini 2.5 Pro",
            "description": "高品質、長文本",
            "max_tokens": 32000
        },
        "gemini-2.0-flash": {
            "display_name": "Gemini 2.0 Flash",
            "description": "上一代快速版本",
            "max_tokens": 8192
        },
        "gemini-1.5-flash": {
            "display_name": "Gemini 1.5 Flash",
            "description": "穩定版",
            "max_tokens": 8192
        },
        "gemini-1.5-pro": {
            "display_name": "Gemini 1.5 Pro",
            "description": "穩定高品質",
            "max_tokens": 32000
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Google Gemini 客戶端

        Args:
            api_key: Google AI Studio API Key (如果不提供，會從環境變數讀取)
        """
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        if not self.api_key:
            raise ValueError("Google AI API Key is required. Set GOOGLE_AI_API_KEY environment variable or pass api_key parameter.")
        
        # 配置 API Key
        genai.configure(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash"  # 預設模型

    def set_model(self, model_name: str):
        """設定使用的模型"""
        if model_name not in self.MODELS:
            raise ValueError(f"Unsupported model: {model_name}. Available: {list(self.MODELS.keys())}")
        self.model_name = model_name

    def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        生成內容

        Args:
            prompt: 使用者輸入的提示詞
            model: 模型名稱 (如果不提供，使用預設)
            system_prompt: 系統提示詞
            temperature: 創意度 (0-1)
            max_tokens: 最大輸出 tokens

        Returns:
            生成的文字內容
        """
        import sys
        model_name = model or self.model_name
        
        print(f"[GoogleGeminiClient] generate_content called with model={model_name}", file=sys.stderr)
        
        # 構建完整提示詞
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        try:
            # 取得模型
            model_instance = genai.GenerativeModel(model_name)

            # 生成配置
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or self.MODELS.get(model_name, {}).get("max_tokens", 8192)
            )

            # 生成內容
            print(f"[GoogleGeminiClient] Calling Gemini API...", file=sys.stderr)
            response = model_instance.generate_content(
                full_prompt,
                generation_config=generation_config
            )

            print(f"[GoogleGeminiClient] Response received, length={len(response.text) if response.text else 0}", file=sys.stderr)
            return response.text
            
        except Exception as e:
            print(f"[GoogleGeminiClient] ERROR: {type(e).__name__}: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise

    def test_connection(self) -> Dict:
        """
        測試連線

        Returns:
            測試結果字典
        """
        try:
            # 簡單測試
            response = self.generate_content(
                prompt="Hello, respond with 'Connection successful!' in exactly those words.",
                temperature=0
            )
            
            return {
                "success": True,
                "message": "Connected to Google Gemini API",
                "response": response[:100],
                "model": self.model_name
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "model": self.model_name
            }

    @classmethod
    def get_available_models(cls) -> Dict:
        """取得可用模型列表"""
        return cls.MODELS


# ============================================================
# 測試用函數
# ============================================================
def test_gemini_client():
    """測試 Google Gemini 客戶端"""
    print("=" * 60)
    print("💎 Google Gemini Direct Client Test")
    print("=" * 60)

    try:
        client = GoogleGeminiClient()
        
        print("\n📡 Testing connection...")
        result = client.test_connection()
        
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"   Model: {result['model']}")
            print(f"   Response: {result['response']}")
        else:
            print(f"❌ {result['message']}")

        print("\n📝 Available models:")
        for name, info in client.MODELS.items():
            print(f"   - {name}: {info['description']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_gemini_client()
