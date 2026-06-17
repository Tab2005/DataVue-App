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

    # 本地備份清單 - 當同步失敗時作為最低限度支援
    MODELS = {
        "models/gemini-1.5-flash": {
            "display_name": "Gemini 1.5 Flash",
            "description": "本地預設模型 (同步失敗)",
            "max_tokens": 8192,
            "provider": "google"
        },
        "models/gemini-2.0-flash": {
            "display_name": "Gemini 2.0 Flash",
            "description": "本地預設模型 (同步失敗)",
            "max_tokens": 8192,
            "provider": "google"
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        """初始化 Google Gemini 客戶端"""
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("ZEABUR_AI_HUB_API_KEY")
        if not self.api_key:
            self.client = None
            return
        
        try:
            # 確保 API KEY 是乾淨的字串
            clean_key = self.api_key.strip()
            self.client = genai.Client(api_key=clean_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini Client: {e}")
            self.client = None
            
        self.model_name = "models/gemini-1.5-flash" 

    def fetch_remote_models(self) -> Dict[str, Dict]:
        """從 Google 伺服器同步模型"""
        if not self.client:
            logger.warning("[GoogleGeminiClient] Client is None, returning fallback models.")
            return self.MODELS

        try:
            logger.info("[GoogleGeminiClient] Requesting remote models via SDK...")
            # 強制迭代所有分頁
            remote_models = list(self.client.models.list())
            merged_models = {}
            
            logger.debug(f"[GoogleGeminiClient] SDK returned {len(remote_models)} raw models.")
            
            for m in remote_models:
                full_name = m.name 
                short_id = full_name.split('/')[-1]
                
                lower_name = full_name.lower()
                # 只要名稱包含 gemini 或 gemma 就納入，不再做嚴格的方法檢查
                if 'gemini' not in lower_name and 'gemma' not in lower_name:
                    continue

                display_name = m.display_name or short_id
                
                # 針對 Gemma 系列模型標記星星
                is_gemma = 'gemma' in lower_name or 'gemma' in display_name.lower()
                if is_gemma:
                    display_name = f"⭐ {display_name}"
                
                merged_models[full_name] = {
                    "display_name": display_name,
                    "description": f"{display_name} (同步自 Google)",
                    "max_tokens": getattr(m, 'output_token_limit', 8192) or 8192,
                    "provider": "google",
                    "is_gemma": is_gemma
                }

            if not merged_models:
                logger.warning("[GoogleGeminiClient] No eligible models found in remote list.")
                return self.MODELS

            # 排序：Gemini 優先於 Gemma -> Flash 優先 -> Gemini 1.5 優先
            sorted_keys = sorted(
                merged_models.keys(),
                key=lambda k: (
                    merged_models[k].get('is_gemma', False), # False (Gemini) < True (Gemma)
                    not 'flash' in k.lower(),                 # False (Flash) < True
                    not 'gemini-1.5' in k.lower(),            # False (1.5) < True
                    merged_models[k]['display_name']
                )
            )
            
            return {k: merged_models[k] for k in sorted_keys}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[GoogleGeminiClient] SYNCHRONIZATION FAILED: {error_msg}")
            # 將錯誤訊息放進清單中，讓前端使用者能看見
            error_list = self.MODELS.copy()
            error_list["error_info"] = {
                "display_name": "❌ 同步異常 (點此看細節)",
                "description": f"原因: {error_msg}",
                "max_tokens": 0,
                "provider": "google"
            }
            return error_list

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
        # 修正 ID 格式
        if not model_to_use.startswith('models/'):
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
            logger.error(f"[GoogleGeminiClient] Generation error: {str(e)}")
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
