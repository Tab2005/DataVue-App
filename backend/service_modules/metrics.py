"""
Metrics Calculator Module

This module contains metric calculation and formatting logic.
Separated from API calls for better maintainability and testability.
"""
from typing import Dict, List, Any, Optional, Union


class MetricsCalculator:
    """Handles metric calculations and formatting for Facebook Ads data."""
    
    @staticmethod
    def process_actions(data: dict) -> dict:
        """
        Parse 'actions' and 'action_values' lists into dictionaries.
        
        Args:
            data: Raw insights data from Facebook API
            
        Returns:
            dict with parsed action data:
            {
                'actions': {'purchase': 10, 'add_to_cart': 25, ...},
                'action_values': {'purchase': 500.00, ...}
            }
        """
        result = {'actions': {}, 'action_values': {}}
        
        # Process actions
        for action in data.get('actions', []):
            action_type = action.get('action_type', '')
            try:
                result['actions'][action_type] = float(action.get('value', 0))
            except (ValueError, TypeError):
                result['actions'][action_type] = 0
        
        # Process action values
        for action in data.get('action_values', []):
            action_type = action.get('action_type', '')
            try:
                result['action_values'][action_type] = float(action.get('value', 0))
            except (ValueError, TypeError):
                result['action_values'][action_type] = 0
        
        return result
    
    @staticmethod
    def calculate_change(current: float, previous: float) -> str:
        """
        Calculate percentage change between two values.
        
        Args:
            current: Current period value
            previous: Previous period value
            
        Returns:
            String percentage change (e.g., "+15.0%", "-1.2%", "0%")
        """
        if previous == 0:
            if current == 0:
                return "0%"
            return "+100%" if current > 0 else "-100%"
        
        change = ((current - previous) / previous) * 100
        sign = "+" if change > 0 else ""
        return f"{sign}{change:.1f}%"
    
    @staticmethod
    def calculate_derived_metrics(data: dict) -> dict:
        """
        Calculate derived metrics from raw Facebook data.
        
        Args:
            data: Raw insights data with actions parsed
            
        Returns:
            dict with calculated metrics
        """
        result = {}
        actions = data.get('actions', {})
        action_values = data.get('action_values', {})
        
        # Safe float conversion
        def safe_float(value, default=0.0):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        impressions = safe_float(data.get('impressions', 0))
        clicks = safe_float(data.get('clicks', 0))
        link_clicks = safe_float(actions.get('link_click', 0))
        spend = safe_float(data.get('spend', 0))
        
        # E-commerce metrics
        purchases = safe_float(actions.get('purchase', 0) or actions.get('omni_purchase', 0))
        add_to_cart = safe_float(actions.get('add_to_cart', 0) or actions.get('omni_add_to_cart', 0))
        view_content = safe_float(actions.get('view_content', 0))
        initiate_checkout = safe_float(actions.get('initiate_checkout', 0))
        
        purchase_value = safe_float(action_values.get('purchase', 0) or action_values.get('omni_purchase', 0))
        atc_value = safe_float(action_values.get('add_to_cart', 0) or action_values.get('omni_add_to_cart', 0))
        
        # Calculated metrics
        result['ctr'] = (link_clicks / impressions * 100) if impressions > 0 else 0
        result['cpc'] = (spend / link_clicks) if link_clicks > 0 else 0
        result['cpm'] = (spend / impressions * 1000) if impressions > 0 else 0
        result['roas'] = (purchase_value / spend) if spend > 0 else 0
        result['cpa'] = (spend / purchases) if purchases > 0 else 0
        result['cost_per_atc'] = (spend / add_to_cart) if add_to_cart > 0 else 0
        result['aov'] = (purchase_value / purchases) if purchases > 0 else 0
        
        # Funnel rates
        result['view_to_cart_rate'] = (add_to_cart / view_content * 100) if view_content > 0 else 0
        result['cart_to_purchase_rate'] = (purchases / add_to_cart * 100) if add_to_cart > 0 else 0
        result['cart_value_realization_rate'] = (purchase_value / atc_value * 100) if atc_value > 0 else 0
        
        # Store raw values too
        result['purchases'] = purchases
        result['add_to_cart'] = add_to_cart
        result['view_content'] = view_content
        result['purchase_value'] = purchase_value
        result['link_clicks'] = link_clicks
        
        return result
    
    @staticmethod
    def format_kpi(
        current: dict, 
        previous: dict, 
        label: str, 
        value: float, 
        prev_value: float = 0,
        is_currency: bool = False,
        is_percent: bool = False,
        is_inverse: bool = False
    ) -> dict:
        """
        Format a single KPI for frontend display.
        
        Args:
            current: Current period data
            previous: Previous period data
            label: Display label for the metric
            value: Current value
            prev_value: Previous value for comparison
            is_currency: Whether to format as currency
            is_percent: Whether to format as percentage
            is_inverse: Whether lower is better (e.g., cost metrics)
            
        Returns:
            dict with formatted KPI data
        """
        change = MetricsCalculator.calculate_change(value, prev_value)
        change_float = float(change.replace('%', '').replace('+', '')) if change != "0%" else 0
        
        # Determine if increase is good or bad
        is_increase = change_float > 0
        is_positive = is_increase if not is_inverse else not is_increase
        
        # Format value
        def format_number(n, for_display=True):
            if is_percent:
                return f"{n:.2f}%" if for_display else round(n, 2)
            elif is_currency:
                return f"${n:,.2f}" if for_display else round(n, 2)
            elif n >= 1000000:
                return f"{n/1000000:.1f}M" if for_display else round(n, 2)
            elif n >= 1000:
                return f"{n/1000:.1f}K" if for_display else round(n, 2)
            else:
                return f"{n:,.0f}" if for_display else round(n, 2)
        
        return {
            "value": format_number(value),
            "previous": format_number(prev_value),
            "diff": format_number(abs(value - prev_value)),
            "change": change,
            "is_increase": is_increase,
            "is_positive": is_positive,
            "raw_value": round(value, 2),
            "raw_previous": round(prev_value, 2)
        }
    
    @staticmethod
    def format_chart_data(data_list: list, metrics: list = None) -> list:
        """
        Format daily data for chart display.
        
        Args:
            data_list: List of daily insight data
            metrics: List of metric names to include (default: ['spend', 'impressions', 'clicks'])
            
        Returns:
            list of formatted chart data points
        """
        if metrics is None:
            metrics = ['spend', 'impressions', 'clicks']
        
        result = []
        for item in data_list:
            point = {
                'date': item.get('date_start', 'Unknown'),
                'label': item.get('date_start', 'Unknown')
            }
            for metric in metrics:
                try:
                    point[metric] = float(item.get(metric, 0))
                except (ValueError, TypeError):
                    point[metric] = 0
            result.append(point)
        
        return result
    
    @staticmethod
    def merge_trend_data(current_data: list, previous_data: list) -> list:
        """
        Merge current and previous period data by day index for trend comparison.
        
        Args:
            current_data: Current period daily data
            previous_data: Previous period daily data
            
        Returns:
            list of merged data with current and previous values
        """
        result = []
        max_len = max(len(current_data), len(previous_data))
        
        for i in range(max_len):
            point = {"day_index": i + 1}
            
            if i < len(current_data):
                cur = current_data[i]
                point['current_date'] = cur.get('date_start', '')
                point['current_spend'] = float(cur.get('spend', 0))
                point['current_impressions'] = int(cur.get('impressions', 0))
            
            if i < len(previous_data):
                prev = previous_data[i]
                point['previous_date'] = prev.get('date_start', '')
                point['previous_spend'] = float(prev.get('spend', 0))
                point['previous_impressions'] = int(prev.get('impressions', 0))
            
            result.append(point)
        
        return result
