# config.py - Enhanced configuration with Claude API instead of Gemini
import streamlit as st
import anthropic

# API Keys
CLAUDE_API_KEY = "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"  # Replace with your actual Claude API key
ALPHA_VANTAGE_API_KEY = "NLKISJ9TBY2KCC6D"

# Configure the Claude API
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
MODEL_NAME = 'claude-3-5-sonnet-20241022'  # or claude-3-opus-20240229 for more powerful analysis

# Analysis weights for different strategies (Technical + Fundamental + Sentiment)
ANALYSIS_WEIGHTS = {
    'Swing Trading': {'technical': 60, 'fundamental': 25, 'sentiment': 15},
    'Value Investing': {'technical': 20, 'fundamental': 65, 'sentiment': 15},
    'Growth Investing': {'technical': 30, 'fundamental': 55, 'sentiment': 15},
    'Balanced Approach': {'technical': 35, 'fundamental': 45, 'sentiment': 20}
}

# Technical indicator weights by strategy (0-1 scale, only for SELECTED indicators)
TECHNICAL_INDICATOR_WEIGHTS = {
    'Swing Trading': {
        # Moving Averages - moderate importance for swing trading
        '20-Day SMA': 0.7, '20-Day EMA': 0.8, '50-Day SMA': 0.6, '200-Day SMA': 0.4,
        # Volatility - very important for swing entries
        '20-Day Bollinger Bands': 0.9, 'ATR (Average True Range)': 0.8,
        # Momentum - critical for swing trading
        'RSI': 1.0, 'MACD': 1.0, 'Stochastic': 0.9,
        # Volume - important for confirming breakouts
        'VWAP': 0.8, 'Volume SMA': 0.7
    },
    'Value Investing': {
        # Moving Averages - long-term trends matter most
        '20-Day SMA': 0.5, '20-Day EMA': 0.4, '50-Day SMA': 0.7, '200-Day SMA': 1.0,
        # Volatility - less important for long-term value
        '20-Day Bollinger Bands': 0.6, 'ATR (Average True Range)': 0.4,
        # Momentum - moderate importance for entry timing
        'RSI': 0.8, 'MACD': 0.6, 'Stochastic': 0.5,
        # Volume - less critical for value investing
        'VWAP': 0.4, 'Volume SMA': 0.3
    },
    'Growth Investing': {
        # Moving Averages - trend direction is important
        '20-Day SMA': 0.8, '20-Day EMA': 0.9, '50-Day SMA': 0.8, '200-Day SMA': 0.7,
        # Volatility - moderate importance
        '20-Day Bollinger Bands': 0.7, 'ATR (Average True Range)': 0.6,
        # Momentum - important for growth momentum
        'RSI': 0.9, 'MACD': 0.9, 'Stochastic': 0.7,
        # Volume - important for confirming growth
        'VWAP': 0.7, 'Volume SMA': 0.6
    },
    'Balanced Approach': {
        # Moving Averages - balanced importance
        '20-Day SMA': 0.7, '20-Day EMA': 0.7, '50-Day SMA': 0.7, '200-Day SMA': 0.6,
        # Volatility - balanced
        '20-Day Bollinger Bands': 0.7, 'ATR (Average True Range)': 0.6,
        # Momentum - balanced
        'RSI': 0.8, 'MACD': 0.8, 'Stochastic': 0.7,
        # Volume - balanced
        'VWAP': 0.7, 'Volume SMA': 0.6
    }
}

# Fundamental ratio weights by strategy (0-1 scale)
FUNDAMENTAL_RATIO_WEIGHTS = {
    'Swing Trading': {
        # Valuation - less important for short-term trading
        'PE_Ratio': 0.4, 'PB_Ratio': 0.3, 'Market_Cap': 0.5,
        # Profitability - moderate importance
        'ROE': 0.6, 'Profit_Margin': 0.5, 'ROA': 0.4,
        # Financial Health - important for avoiding bad stocks
        'Current_Ratio': 0.7, 'Debt_to_Equity': 0.8,
        # Growth - moderate importance
        'Revenue_Growth': 0.6, 'EPS_Growth': 0.6, 'Free_Cash_Flow': 0.5,
        # Income - less important for swing trading
        'Dividend_Yield': 0.2, 'Payout_Ratio': 0.2
    },
    'Value Investing': {
        # Valuation - critical for value investing
        'PE_Ratio': 1.0, 'PB_Ratio': 1.0, 'Market_Cap': 0.7,
        # Profitability - very important
        'ROE': 0.9, 'Profit_Margin': 0.8, 'ROA': 0.8,
        # Financial Health - absolutely critical
        'Current_Ratio': 1.0, 'Debt_to_Equity': 1.0,
        # Growth - moderate importance (value can have slow growth)
        'Revenue_Growth': 0.5, 'EPS_Growth': 0.6, 'Free_Cash_Flow': 0.9,
        # Income - very important for value investors
        'Dividend_Yield': 0.9, 'Payout_Ratio': 0.8
    },
    'Growth Investing': {
        # Valuation - less important (growth stocks trade at premium)
        'PE_Ratio': 0.5, 'PB_Ratio': 0.4, 'Market_Cap': 0.6,
        # Profitability - important but growth trumps current profits
        'ROE': 0.7, 'Profit_Margin': 0.6, 'ROA': 0.6,
        # Financial Health - important to sustain growth
        'Current_Ratio': 0.8, 'Debt_to_Equity': 0.7,
        # Growth - absolutely critical
        'Revenue_Growth': 1.0, 'EPS_Growth': 1.0, 'Free_Cash_Flow': 0.8,
        # Income - usually not important for growth stocks
        'Dividend_Yield': 0.3, 'Payout_Ratio': 0.2
    },
    'Balanced Approach': {
        # Valuation - balanced importance
        'PE_Ratio': 0.7, 'PB_Ratio': 0.6, 'Market_Cap': 0.6,
        # Profitability - balanced
        'ROE': 0.8, 'Profit_Margin': 0.7, 'ROA': 0.7,
        # Financial Health - balanced
        'Current_Ratio': 0.8, 'Debt_to_Equity': 0.8,
        # Growth - balanced
        'Revenue_Growth': 0.7, 'EPS_Growth': 0.7, 'Free_Cash_Flow': 0.7,
        # Income - balanced
        'Dividend_Yield': 0.6, 'Payout_Ratio': 0.5
    }
}

# Growth metrics weights by strategy
GROWTH_METRICS_WEIGHTS = {
    'Swing Trading': {
        'Revenue_Per_Share': 0.5, 'EPS': 0.6, 'Dividend_Yield': 0.2,
        'Free_Cash_Flow': 0.5, 'Profit_Margin': 0.6
    },
    'Value Investing': {
        'Revenue_Per_Share': 0.6, 'EPS': 0.8, 'Dividend_Yield': 0.9,
        'Free_Cash_Flow': 1.0, 'Profit_Margin': 0.8
    },
    'Growth Investing': {
        'Revenue_Per_Share': 1.0, 'EPS': 1.0, 'Dividend_Yield': 0.2,
        'Free_Cash_Flow': 0.8, 'Profit_Margin': 0.7
    },
    'Balanced Approach': {
        'Revenue_Per_Share': 0.7, 'EPS': 0.8, 'Dividend_Yield': 0.6,
        'Free_Cash_Flow': 0.8, 'Profit_Margin': 0.7
    }
}

def get_strategy_weights(investing_type, selected_indicators=None, available_ratios=None):
    """
    Get weighted scores based on investment strategy and selected indicators/ratios
    Only applies weights to indicators/ratios that are actually selected/available
    """
    weights = {
        'technical_indicators': {},
        'fundamental_ratios': {},
        'growth_metrics': {}
    }
    
    # Technical indicator weights (only for selected indicators)
    if selected_indicators:
        tech_weights = TECHNICAL_INDICATOR_WEIGHTS.get(investing_type, {})
        for indicator in selected_indicators:
            if indicator in tech_weights:
                weights['technical_indicators'][indicator] = tech_weights[indicator]
    
    # Fundamental ratio weights (only for available ratios)
    if available_ratios:
        fund_weights = FUNDAMENTAL_RATIO_WEIGHTS.get(investing_type, {})
        growth_weights = GROWTH_METRICS_WEIGHTS.get(investing_type, {})
        
        for ratio in available_ratios:
            if ratio in fund_weights:
                weights['fundamental_ratios'][ratio] = fund_weights[ratio]
            if ratio in growth_weights:
                weights['growth_metrics'][ratio] = growth_weights[ratio]
    
    return weights

def calculate_weighted_technical_score(indicator_results, selected_indicators, investing_type):
    """Calculate weighted technical score based on strategy and selected indicators"""
    if not indicator_results or not selected_indicators:
        return 0.0
    
    weights = TECHNICAL_INDICATOR_WEIGHTS.get(investing_type, {})
    total_score = 0.0
    total_weight = 0.0
    
    for indicator in selected_indicators:
        if indicator in weights and indicator in indicator_results:
            # Convert indicator result to score (0-1)
            indicator_score = convert_indicator_to_score(indicator, indicator_results[indicator])
            weight = weights[indicator]
            
            total_score += indicator_score * weight
            total_weight += weight
    
    return total_score / total_weight if total_weight > 0 else 0.0

def convert_indicator_to_score(indicator_name, indicator_data):
    """Convert indicator data to normalized score (0-1)"""
    if not indicator_data:
        return 0.5  # Neutral if no data
    
    try:
        if indicator_name == 'RSI':
            rsi_val = indicator_data.get('current', 50)
            if rsi_val < 30:
                return 0.8  # Oversold - good for buying
            elif rsi_val > 70:
                return 0.2  # Overbought - bearish
            else:
                return 0.5  # Neutral
        
        elif indicator_name == 'MACD':
            macd_val = indicator_data.get('macd', 0)
            signal_val = indicator_data.get('signal', 0)
            if macd_val > signal_val:
                return 0.7  # Bullish
            else:
                return 0.3  # Bearish
        
        elif 'SMA' in indicator_name or 'EMA' in indicator_name:
            # Assume we have current price vs MA
            current = indicator_data.get('current')
            if current and 'current_price' in indicator_data:
                price = indicator_data['current_price']
                if price > current:
                    return 0.7  # Above MA - bullish
                else:
                    return 0.3  # Below MA - bearish
        
        elif 'Bollinger' in indicator_name:
            position = indicator_data.get('position', 0.5)
            if position < 0.2:
                return 0.8  # Near lower band - oversold
            elif position > 0.8:
                return 0.2  # Near upper band - overbought
            else:
                return 0.5  # Middle zone
        
        # Default neutral score
        return 0.5
        
    except Exception:
        return 0.5