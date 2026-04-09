"""
Google Gemini 直連客戶端
直接使用 Google AI Studio 的 API Key 呼叫 Gemini 模型
"""
import google.genai as genai
from google.genai import types
import logging
from typing import Optional, Dict, List, Union
import os

logger = logging.getLogger(__name__)


class GoogleGeminiClient:
    """Google Gemini 直連客戶端 - 使用 Google AI Studio API Key"""

    # 本地備份清單
    MODELS = {
        "gemini-1.5-flash": {
            "display_name": "Gemini 1.5 Flash",
            "description": "穩定、快速、免費額度高 ✅ 推薦",
            "max_tokens": 8192,
            "provider": "google"
        },
        "gemini-2.0-flash": {
            "display_name": "Gemini 2.0 Flash",
            "description": "最新世代、極速",
            "max_tokens": 8192,
            "provider": "google"
        },
        "gemini-1.5-pro": {
            "display_name": "Gemini 1.5 Pro",
            "description": "高品質、長文本",
            "max_tokens": 32000,
            "provider": "google"
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        """初始化 Google Gemini 客戶端"""
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        if not self.api_key:
            self.client = None
            return
        
        try:
            # 使用新版 SDK 的 Client 模式
            # 注意: 不手動指定 v1beta，讓 SDK 根據模型自動判斷
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini Client: {e}")
            self.client = None
            
        self.model_name = "models/gemini-1.5-flash" 

    def fetch_remote_models(self) -> Dict[str, Dict]:
        """從 Google 伺服器同步最新可用模型清單"""
        if not self.client:
            return self.MODELS

        try:
            remote_models = self.client.models.list()
            merged_models = {}
            
            for m in remote_models:
                # 取得完整名稱 (通常是 models/xxx)
                model_full_name = m.name
                # 取得短名稱 (xxx)
                model_id = model_full_name.split('/')[-1]
                
                # 放寬限制：只要支援生成 (Content, Text, Answer) 都顯示
                methods = m.supported_generation_methods or []
                is_generative = any(method in ['generateContent', 'generateText', 'generateAnswer'] for method in methods)
                
                if is_generative:
                    if model_id in self.MODELS:
                        merged_models[model_full_name] = self.MODELS[model_id].copy()
                        merged_models[model_full_name]["display_name"] = f"{self.MODELS[model_id]['display_name']} (穩定)"
                    else:
                        # 對於 Gemma 或其他新模型
                        display_name = m.display_name or model_id
                        merged_models[model_full_name] = {
                            "display_name": display_name,
                            "description": f"{display_name} (外部同步)",
                            "max_tokens": m.output_token_limit or 8192,
                            "provider": "google"
                        }
            
            logger.info(f"Fetched {len(merged_models)} remote models from Google")
            return merged_models if merged_models else self.MODELS
        except Exception as e:
            logger.error(f"Failed to fetch Google remote models: {e}")
            return self.MODELS

    def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """生成內容"""
        if not self.client:
            raise RuntimeError("Gemini Client not initialized. API Key is missing.")
            
        # 確保傳遞給 SDK 的名稱格式正確
        model_to_use = model or self.model_name
        # 如果模型名稱不包含 models/ 前綴且不是特定路徑，則嘗試補全 (但通常 sync 下來的已經包含了)
        if '/' not in model_to_use:
            model_to_use = f"models/{model_to_use}"

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens or 8192
            )

            # 呼叫新版 SDK
            response = self.client.models.generate_content(
                model=model_to_use,
                contents=prompt,
                config=config
            )

            return response.text
        except Exception as e:
            logger.error(f"[GoogleGeminiClient] ERROR using model {model_to_use}: {str(e)}")
            raise

    def set_model(self, model_name: str):
        """設定目前的模型名稱"""
        self.model_name = model_name

    def get_available_models(self, remote: bool = False) -> Dict[str, Dict]:
        """獲取可用模型列表"""
        if remote:
            return self.fetch_remote_models()
        return self.MODELS.copy()

    def test_connection(self) -> Dict:
        """測試連線"""
        try:
            response = self.generate_content(prompt="OK", temperature=0)
            return {
                "success": True,
                "message": "Connected Successfully!",
                "response": response,
                "model": self.model_name
            }
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {str(e)}", "model": self.model_name}
