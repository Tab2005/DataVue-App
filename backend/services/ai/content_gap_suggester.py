"""
內容缺口文章方向建議器 (Content Gap Article Direction Suggester)
針對頁面「有排名但內文未涵蓋」的關鍵字，用 AI 產生文章方向建議

建議類型:
- expand_existing: 建議補充進現有頁面的段落方向
- new_article: 建議獨立成一篇新文章的方向

參見 docs/37_GSC_內容缺口_AI文章方向建議_實作規劃.md
"""
import json
import logging
from typing import Dict, List, Optional
from .zeabur_client import ZeaburAIClient

logger = logging.getLogger(__name__)


class AIContentGapSuggester:
    """使用 AI 模型將內容缺口關鍵字整理成文章方向建議"""

    SYSTEM_PROMPT = """你是一位幫中小企業老闆／小編規劃文章的內容顧問，講話直白、生活化，不用艱澀的行銷或 SEO 術語轟炸對方。

你會收到一份清單，裡面是某個網頁「有人在 Google 搜這些字、也搜得到這個網頁，但頁面內文完全沒寫到」的關鍵字，每個關鍵字附帶點擊數、曝光數與平均排名。

你的任務：
1. 把講同一件事、同一類問題的關鍵字歸在一起，能分幾組就分幾組，不要硬湊成固定數量。
2. 針對每一組，判斷應該：
   - "expand_existing"：份量不多、跟這頁主題很搭，建議直接在現有頁面補寫一段就好。
   - "new_article"：內容夠寫成一整篇、或跟這頁主題差比較多，建議獨立寫一篇新文章。
3. 為每一組產生：
   - 標題：寫得像真正會發布的文章標題，讀者一看就知道點進去會看到什麼，**不要**寫成「XX 主題分析」「關於 XX 之探討」這種報告式標題。
   - 大綱：3-6 條，每條都是「這段實際會寫的內容」，具體到可以直接照著動筆的程度（例如「怎麼挑」「常見情境有哪些」「多少錢比較划算」），**不要**寫「探討可行性」「分析其重要性」這種空泛講法。
   - 涉及的關鍵字清單。
   - 一句話白話理由：講人話說明為什麼這樣分／這樣寫，**避免**使用「語意相關性」「內容策略」「使用者意圖」這類術語，改用「這些字問的都是同一件事」「這個題目能寫的東西夠多，值得獨立寫一篇」這種說法。
4. 曝光數與點擊數較高的關鍵字群組，代表機會較大，請優先列出。

輸出格式要求 (JSON)：
```json
{
  "suggestions": [
    {
      "type": "expand_existing",
      "title": "建議標題",
      "outline": ["大綱要點 1", "大綱要點 2", "大綱要點 3"],
      "target_keywords": ["關鍵字1", "關鍵字2"],
      "reasoning": "簡短說明為何如此分類"
    }
  ]
}
```

重要規則：
- 只輸出有效的 JSON，不要有其他文字。
- 每個輸入關鍵字最多只能出現在一組建議的 target_keywords 中，不要重複分派。
- 標題、大綱、理由全部用白話繁體中文，避免專業術語；若真的需要提到專業詞，後面要立刻接一句白話解釋，不能只丟術語。
- 若關鍵字彼此差異很大，允許產生多組建議；若高度一致，允許只產生 1 組。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek/deepseek-v4-flash",
        provider: str = "zeabur"
    ):
        """
        初始化文章方向建議器

        Args:
            api_key: API Key (Zeabur AI Hub 或 OpenRouter)
            model: 使用的 AI 模型
            provider: AI 提供者 ("zeabur" 使用 Zeabur AI Hub, "openrouter" 使用 OpenRouter 客戶端)
        """
        self.provider = provider
        self.model = model

        if provider == "openrouter":
            from .openrouter_client import OpenRouterClient
            self.client = OpenRouterClient(api_key=api_key)
            self.client.set_model(model)
        else:
            self.client = ZeaburAIClient(api_key=api_key)

    def suggest_directions(
        self,
        page_url: str,
        page_title: str,
        missing_keywords: List[Dict],
        temperature: float = 0.4
    ) -> Dict:
        """
        將缺口關鍵字整理成文章方向建議

        Args:
            page_url: 頁面 URL
            page_title: 頁面標題
            missing_keywords: 缺口關鍵字列表，格式 [{"query": ..., "clicks": ..., "impressions": ..., "position": ...}]
            temperature: AI 創意度

        Returns:
            {
                "success": True,
                "model": "...",
                "page": "...",
                "suggestions": [...]
            }
        """
        if not missing_keywords:
            return {
                "success": True,
                "model": self.model,
                "page": page_url,
                "suggestions": []
            }

        keywords_text = "\n".join(
            f"- {kw['query']}（點擊:{kw.get('clicks', 0)}, 曝光:{kw.get('impressions', 0)}, 平均排名:{kw.get('position', 0):.1f}）"
            for kw in missing_keywords
        )
        prompt = f"""頁面標題：{page_title or '（無標題）'}
頁面網址：{page_url}

以下是這個頁面「有排名但內文未涵蓋」的關鍵字（共 {len(missing_keywords)} 個）：

{keywords_text}

請依照系統指示，將這些關鍵字整理成文章方向建議。"""

        try:
            response = self._generate_full_content(prompt, temperature)

            parsed = self._parse_json_response(response)

            return {
                "success": True,
                "model": self.model,
                "page": page_url,
                "suggestions": parsed.get("suggestions", [])
            }

        except Exception as e:
            logger.error(f"[AIContentGapSuggester] suggest_directions failed: {e}")
            return {
                "success": False,
                "model": self.model,
                "page": page_url,
                "error": str(e),
                "suggestions": []
            }

    def _generate_full_content(self, prompt: str, temperature: float) -> str:
        """呼叫 AI 模型並回傳完整內容。

        改用串流呼叫（與 ai_service.py 內 GA4 轉換洞察 AI 分析功能相同的呼叫方式），
        而非一次性阻塞呼叫：部分 provider（例如 OpenRouter 上游的免費/限流模型）
        對非串流請求偶爾會回傳無 choices 的空內容，但串流呼叫可正常運作。
        """
        if self.provider == "openrouter":
            chunks = self.client.generate_content_stream(
                prompt=prompt,
                model=self.model,
                temperature=temperature,
                system_prompt=self.SYSTEM_PROMPT
            )
        else:
            chunks = self.client.generate_content(
                prompt=prompt,
                model=self.model,
                temperature=temperature,
                system_prompt=self.SYSTEM_PROMPT,
                stream=True
            )
        return "".join(chunks)

    def _parse_json_response(self, response: str) -> Dict:
        """解析 AI 回應中的 JSON（三層 fallback，沿用 AIIntentClassifier 的模式）"""
        if not response or not response.strip():
            # 常見成因：上游 provider（例如免費/限流模型）沒有實際錯誤碼卻回傳空內容，
            # 明確標示「空回應」而非丟出容易誤導成「JSON 格式錯誤」的訊息。
            raise ValueError("AI provider returned an empty response (no error code) — likely rate-limited or overloaded upstream.")

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(response[start:end + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Failed to parse JSON from response: {response[:200]}...")
