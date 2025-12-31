"""
搜尋意圖分類器 (Search Intent Classifier)
使用 AI 模型分類關鍵字的搜尋意圖類型

意圖類型:
- 🔵 資訊型 (Informational): 用戶想了解某事
- 🟠 商業型 (Commercial): 用戶在評估選項
- 🟢 導航型 (Navigational): 用戶想到達特定網站
- 🔴 交易型 (Transactional): 用戶準備購買/行動
"""
import json
import os
from typing import Dict, List, Optional
from .zeabur_client import ZeaburAIClient


class AIIntentClassifier:
    """使用 AI 模型進行搜尋意圖分類"""

    # 意圖類型定義
    INTENT_TYPES = {
        "informational": {
            "emoji": "🔵",
            "name_zh": "資訊型",
            "name_en": "Informational",
            "description": "用戶想了解某事、尋找資訊"
        },
        "commercial": {
            "emoji": "🟠",
            "name_zh": "商業型",
            "name_en": "Commercial",
            "description": "用戶在評估選項、比較產品"
        },
        "navigational": {
            "emoji": "🟢",
            "name_zh": "導航型",
            "name_en": "Navigational",
            "description": "用戶想到達特定網站或品牌"
        },
        "transactional": {
            "emoji": "🔴",
            "name_zh": "交易型",
            "name_en": "Transactional",
            "description": "用戶準備購買或採取行動"
        }
    }

    # System Prompt 設計
    SYSTEM_PROMPT = """你是一位專業的 SEO 搜尋意圖分析專家。你的任務是分析關鍵字（搜尋查詢）的搜尋意圖類型。

搜尋意圖分為四種類型：
1. **informational** (資訊型): 用戶想了解、學習某事。特徵關鍵字如：如何、是什麼、為什麼、教學、方法、步驟、技巧、入門、指南、how, what, why, guide, tutorial
2. **commercial** (商業型): 用戶正在評估、比較選項。特徵關鍵字如：推薦、評價、比較、最佳、排名、優缺點、vs、best, review, top, alternative
3. **navigational** (導航型): 用戶想到達特定網站或品牌頁面。特徵：包含品牌名稱、官網、登入、website, login
4. **transactional** (交易型): 用戶準備購買或採取具體行動。特徵關鍵字如：購買、價格、費用、下載、報名、訂閱、折扣、優惠、免費、試用、buy, price, discount, download

請根據上述定義，為每個關鍵字判斷其**主要意圖類型**，並給出**四種意圖的分布比例** (總和為 1.0)。

輸出格式要求 (JSON):
```json
{
  "results": [
    {
      "query": "原始關鍵字",
      "primary_intent": "主要意圖類型 (informational/commercial/navigational/transactional)",
      "confidence": 0.85,
      "intent_distribution": {
        "informational": 0.75,
        "commercial": 0.15,
        "navigational": 0.05,
        "transactional": 0.05
      },
      "reasoning": "簡短解釋為何判斷為此意圖"
    }
  ]
}
```

重要規則：
- 只輸出有效的 JSON，不要有其他文字
- intent_distribution 四個值的總和必須等於 1.0
- confidence 範圍為 0-1，表示對主要意圖判斷的信心程度
- reasoning 用繁體中文簡短說明"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ):
        """
        初始化 AI 意圖分類器

        Args:
            api_key: Zeabur AI Hub API Key
            model: 使用的 AI 模型
        """
        self.client = ZeaburAIClient(api_key=api_key)
        self.model = model

    def classify_queries(
        self,
        queries: List[str],
        temperature: float = 0.3
    ) -> Dict:
        """
        批量分類多個關鍵字的搜尋意圖

        Args:
            queries: 關鍵字列表
            temperature: AI 創意度 (建議使用較低值以獲得一致結果)

        Returns:
            {
                "success": True,
                "model": "gemini-2.5-flash",
                "results": [
                    {
                        "query": "...",
                        "primary_intent": "...",
                        "confidence": 0.85,
                        "intent_distribution": {...},
                        "reasoning": "..."
                    }
                ]
            }
        """
        # 構建 prompt
        queries_text = "\n".join([f"- {q}" for q in queries])
        prompt = f"""請分析以下 {len(queries)} 個關鍵字的搜尋意圖：

{queries_text}

請為每個關鍵字判斷主要意圖類型與意圖分布比例。"""

        try:
            # 呼叫 AI
            response = self.client.generate_content(
                prompt=prompt,
                model=self.model,
                temperature=temperature,
                system_prompt=self.SYSTEM_PROMPT
            )

            # 解析 JSON 回應
            parsed = self._parse_json_response(response)

            return {
                "success": True,
                "model": self.model,
                "query_count": len(queries),
                "results": parsed.get("results", [])
            }

        except Exception as e:
            return {
                "success": False,
                "model": self.model,
                "error": str(e),
                "results": []
            }

    def classify_single(self, query: str) -> Dict:
        """
        分類單一關鍵字

        Args:
            query: 單一關鍵字

        Returns:
            分類結果
        """
        result = self.classify_queries([query])
        if result["success"] and result["results"]:
            return {
                "success": True,
                "model": self.model,
                **result["results"][0]
            }
        return result

    def classify_page_queries(
        self,
        page_url: str,
        queries: List[Dict]
    ) -> Dict:
        """
        分析頁面關聯關鍵字的整體意圖

        Args:
            page_url: 頁面 URL
            queries: 關鍵字列表，格式 [{"query": "...", "clicks": 100, "impressions": 1000}]

        Returns:
            {
                "page": "頁面 URL",
                "primary_intent": "主要意圖",
                "intent_distribution": {...},
                "query_intents": [...]
            }
        """
        query_texts = [q["query"] for q in queries]
        result = self.classify_queries(query_texts)

        if not result["success"]:
            return result

        # 計算加權意圖分布 (根據點擊數加權)
        total_clicks = sum(q.get("clicks", 1) for q in queries)
        weighted_distribution = {
            "informational": 0.0,
            "commercial": 0.0,
            "navigational": 0.0,
            "transactional": 0.0
        }

        query_results = result["results"]
        for i, query_result in enumerate(query_results):
            clicks = queries[i].get("clicks", 1) if i < len(queries) else 1
            weight = clicks / total_clicks
            dist = query_result.get("intent_distribution", {})
            for intent in weighted_distribution:
                weighted_distribution[intent] += dist.get(intent, 0.25) * weight

        # 判斷頁面主要意圖
        primary = max(weighted_distribution, key=weighted_distribution.get)

        return {
            "success": True,
            "model": self.model,
            "page": page_url,
            "primary_intent": primary,
            "intent_distribution": weighted_distribution,
            "query_intents": query_results
        }

    def _parse_json_response(self, response: str) -> Dict:
        """
        解析 AI 回應中的 JSON

        Args:
            response: AI 回應文字

        Returns:
            解析後的字典
        """
        # 嘗試直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 嘗試提取 JSON 區塊
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 嘗試找到 { } 區塊
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(response[start:end+1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Failed to parse JSON from response: {response[:200]}...")

    def format_result(self, result: Dict) -> str:
        """
        格式化輸出結果 (適合終端顯示)

        Args:
            result: 分類結果

        Returns:
            格式化的字串
        """
        if not result.get("success"):
            return f"❌ 分類失敗: {result.get('error', 'Unknown error')}"

        output_lines = []
        output_lines.append(f"🤖 Model: {result.get('model', 'Unknown')}")
        output_lines.append("=" * 60)

        for item in result.get("results", []):
            query = item.get("query", "N/A")
            intent = item.get("primary_intent", "unknown")
            confidence = item.get("confidence", 0)
            reasoning = item.get("reasoning", "")

            intent_info = self.INTENT_TYPES.get(intent, {})
            emoji = intent_info.get("emoji", "❓")
            name_zh = intent_info.get("name_zh", intent)

            output_lines.append(f"\n📝 關鍵字: {query}")
            output_lines.append(f"   意圖: {emoji} {name_zh} (confidence: {confidence:.0%})")
            output_lines.append(f"   理由: {reasoning}")

            dist = item.get("intent_distribution", {})
            output_lines.append("   分布:")
            for i_type, i_info in self.INTENT_TYPES.items():
                pct = dist.get(i_type, 0) * 100
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                output_lines.append(
                    f"      {i_info['emoji']} {i_info['name_zh']:4s} {bar} {pct:.0f}%"
                )

        return "\n".join(output_lines)


# ============================================================
# 測試用函數
# ============================================================
def test_intent_classifier():
    """
    測試搜尋意圖分類器
    使用前請先設定環境變數: ZEABUR_AI_HUB_API_KEY
    """
    print("=" * 60)
    print("🔍 搜尋意圖分類測試 (Search Intent Classification Test)")
    print("=" * 60)

    # 測試關鍵字範例
    test_queries = [
        # 資訊型
        "如何設定 Facebook 廣告",
        "什麼是 ROAS",
        "SEO 教學 入門",

        # 商業型
        "最佳 SEO 工具推薦",
        "GA4 vs Google Analytics 比較",
        "2024 行銷工具排名",

        # 導航型
        "Facebook 廣告管理員",
        "Google Search Console 登入",

        # 交易型
        "購買 SEO 課程",
        "Ahrefs 價格",
        "免費試用 Semrush"
    ]

    try:
        # 初始化分類器
        classifier = AIIntentClassifier()

        print(f"\n📊 測試 {len(test_queries)} 個關鍵字...\n")

        # 批量分類
        result = classifier.classify_queries(test_queries)

        # 格式化輸出
        print(classifier.format_result(result))

        print("\n" + "=" * 60)
        print("✅ 測試完成!")

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_intent_classifier()
