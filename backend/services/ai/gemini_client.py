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
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        """初始化 Google Gemini 客戶端"""
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        if not self.api_key:
            self.client = None
            return
        
        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini Client: {e}")
            self.client = None
            
        self.model_name = "models/gemini-1.5-flash" 

    def fetch_remote_models(self) -> Dict[str, Dict]:
        """從 Google 伺服器同步所有可用模型清單 (包含 Gemma 系列)"""
        if not self.client:
            return self.MODELS

        try:
            logger.info("[GoogleGeminiClient] Fetching all remote models (pagination-aware)...")
            
            # 使用 list() 獲取分頁物件
            remote_models = self.client.models.list()
            merged_models = {}
            
            # Pager 會自動迭代所有分頁
            for m in remote_models:
                full_name = m.name # 格式如 models/gemini-pro
                short_id = full_name.split('/')[-1]
                
                # 跳過不支援生成的模型 (如 embedding, text-moderation 等)
                # 但 Gemma 4 應該支援生成，所以我們保留它
                methods = m.supported_generation_methods or []
                is_generative = any(met in ['generateContent', 'generateText', 'generateAnswer'] for met in methods)
                
                if not is_generative and 'gemma' not in full_name.lower():
                    continue

                if short_id in self.MODELS:
                    merged_models[full_name] = self.MODELS[short_id].copy()
                    merged_models[full_name]["display_name"] = f"{self.MODELS[short_id]['display_name']} (穩定)"
                else:
                    display_name = m.display_name or short_id
                    
                    # 針對 Gemma 進行顯示優化
                    if 'gemma' in full_name.lower() or 'gemma' in display_name.lower():
                        display_name = f"💎 {display_name}"
                    
                    merged_models[full_name] = {
                        "display_name": display_name,
                        "description": f"{display_name} (外部同步)",
                        "max_tokens": getattr(m, 'output_token_limit', 8192) or 8192,
                        "provider": "google"
                    }
            
            # --- 排序邏輯 ---
            # 依據 display_name 進行排序，並將推薦的模型放在最前面
            sorted_keys = sorted(
                merged_models.keys(), 
                key=lambda k: (
                    not k.endswith('flash'), # Flash 優先
                    not 'gemini-1.5' in k,   # 1.5 優先
                    merged_models[k]['display_name'].lower()
                )
            )
            
            final_models = {k: merged_models[k] for k in sorted_keys}
            
            logger.info(f"[GoogleGeminiClient] Successfully fetched and sorted {len(final_models)} models.")
            return final_models if final_models else self.MODELS
        except Exception as e:
            logger.error(f"[GoogleGeminiClient] Failed to fetch Google remote models: {e}")
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
            raise RuntimeError("Gemini Client not initialized.")
            
        model_to_use = model or self.model_name
        if '/' not in model_to_use:
            model_to_use = f"models/{model_to_use}"

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens or 8192
            )

            response = self.client.models.generate_content(
                model=model_to_use,
                contents=prompt,
                config=config
            )

            return response.text
        except Exception as e:
            logger.error(f"[GoogleGeminiClient] Error using model {model_to_use}: {str(e)}")
            raise

    def set_model(self, model_name: str):
        self.model_name = model_name

    def get_available_models(self, remote: bool = False) -> Dict[str, Dict]:
        if remote:
            return self.fetch_remote_models()
        return self.MODELS.copy()

    def test_connection(self) -> Dict:
        try:
            response = self.generate_content(prompt="Hi", temperature=0, max_tokens=5)
            return {
                "success": True,
                "message": f"Connected Successfully! Using {self.model_name}",
                "response": response,
                "model": self.model_name
            }
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {str(e)}", "model": self.model_name}
