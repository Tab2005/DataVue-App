import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add current directory to path so we can import services
sys.path.append(os.getcwd())

from services import FacebookService

class TestFacebookServicePhase5(unittest.TestCase):

    def setUp(self):
        self.mock_current_data = {
            "spend": "100.0",
            "impressions": "1000",
            "clicks": "50",
            "reach": "800",
            "cpc": "2.0",
            "cpm": "10.0",
            "ctr": "5.0",
            "date_start": "2023-12-01",
            "date_stop": "2023-12-07",
            "actions": [
                {"action_type": "purchase", "value": "5"},
                {"action_type": "add_to_cart", "value": "10"}
            ],
            "purchase_roas": [{"action_type": "purchase_roas", "value": "2.5"}]
        }
        
        self.mock_prev_data = {
            "spend": "80.0",
            "impressions": "800",
            # clicks/reach missing to test fallback
            "actions": [
                {"action_type": "purchase", "value": "4"},
                {"action_type": "add_to_cart", "value": "8"}
            ],
             "purchase_roas": [{"action_type": "purchase_roas", "value": "2.0"}]
        }
        
        self.mock_trend = [
            {"date_start": "2023-12-01", "spend": "10"},
            {"date_start": "2023-12-02", "spend": "20"}
        ]

    @patch('services.requests.get')
    def test_get_account_insights_logic(self, mock_get):
        # Setup Mock Responses
        # We need to mock 3 calls: Current KPI, Previous KPI, Trend
        
        # Mock 1: Current KPI
        mock_resp_1 = MagicMock()
        mock_resp_1.json.return_value = {"data": [self.mock_current_data]}
        
        # Mock 2: Previous KPI
        mock_resp_2 = MagicMock()
        mock_resp_2.json.return_value = {"data": [self.mock_prev_data]}
        
        # Mock 3: Trend
        mock_resp_3 = MagicMock()
        mock_resp_3.json.return_value = {"data": self.mock_trend}
        
        mock_get.side_effect = [mock_resp_1, mock_resp_2, mock_resp_3]

        with patch.object(FacebookService, 'get_headers', return_value={"Authorization": "Bearer token"}):
            result = FacebookService.get_account_insights("act_123", "user_123", days=7)
            
            self.assertIsNotNone(result)
            kpi = result["kpi"]
            
            # Verify 8 Metrics exist
            self.assertEqual(len(kpi), 8)
            
            # 1. Spend: 100 vs 80 -> +25%
            spend = next(k for k in kpi if "Spend" in k["label"])
            self.assertEqual(spend["value"], "$100.00")
            self.assertEqual(spend["sub_value"], "80.00")
            self.assertEqual(spend["change"], "+25.00%")
            
            # 2. Purchase (Action parsing): 5 vs 4 -> +25%
            purchases = next(k for k in kpi if "Purchases" in k["label"])
            self.assertEqual(purchases["value"], "5.00")
            self.assertEqual(purchases["change"], "+25.00%")
            
            # 3. ROAS: 2.5 vs 2.0 -> +25%
            roas = next(k for k in kpi if "ROAS" in k["label"])
            self.assertEqual(roas["value"], "2.50")
            
            print("\n✅ Verification Passed: Comparison & Parsing Logic is correct.")

if __name__ == '__main__':
    unittest.main()
