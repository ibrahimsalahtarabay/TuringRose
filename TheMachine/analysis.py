# analysis.py - Fixed Technical analysis without streamlit dependencies
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
from config import gen_model

def calculate_rsi(prices, window=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_stochastic(high, low, close, k_window=14, d_window=3):
    """Calculate Stochastic Oscillator"""
    lowest_low = low.rolling(window=k_window).min()
    highest_high = high.rolling(window=k_window).max()
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_window).mean()
    return k_percent, d_percent

def calculate_atr(high, low, close, window=14):
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    return atr

def analyze_ticker(ticker, data, indicators, indicator_params=None):
    """Enhanced analyze function with comprehensive technical indicators"""
    
    # Default parameters if none provided
    if indicator_params is None:
        indicator_params = {
            'rsi_period': 14, 'macd_fast': 12, 'macd_slow': 26, 
            'bb_period': 20, 'bb_std': 2.0
        }
    
    # Build candlestick chart
    fig = go.Figure(data=[
        go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'],
            low=data['Low'], close=data['Close'], name="Candlestick"
        )
    ])

    # Store indicator values for analysis
    indicator_values = {}
    
    # Calculate and add technical indicators
    def add_indicator(indicator):
        if indicator == "20-Day SMA":
            sma = data['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(x=data.index, y=sma, mode='lines', name='SMA (20)', line=dict(color='blue')))
            indicator_values['SMA_20'] = {
                'current': sma.iloc[-1] if not sma.empty else None,
                'previous': sma.iloc[-2] if len(sma) > 1 else None,
                'slope': (sma.iloc[-1] - sma.iloc[-5]) if len(sma) > 5 else None
            }
            
        elif indicator == "20-Day EMA":
            ema = data['Close'].ewm(span=20).mean()
            fig.add_trace(go.Scatter(x=data.index, y=ema, mode='lines', name='EMA (20)', line=dict(color='orange')))
            indicator_values['EMA_20'] = {
                'current': ema.iloc[-1] if not ema.empty else None,
                'previous': ema.iloc[-2] if len(ema) > 1 else None,
                'slope': (ema.iloc[-1] - ema.iloc[-5]) if len(ema) > 5 else None
            }
            
        elif indicator == "50-Day SMA":
            sma_50 = data['Close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(x=data.index, y=sma_50, mode='lines', name='SMA (50)', line=dict(color='darkblue')))
            indicator_values['SMA_50'] = {
                'current': sma_50.iloc[-1] if not sma_50.empty else None,
                'slope': (sma_50.iloc[-1] - sma_50.iloc[-10]) if len(sma_50) > 10 else None
            }
            
        elif indicator == "200-Day SMA":
            sma_200 = data['Close'].rolling(window=200).mean()
            fig.add_trace(go.Scatter(x=data.index, y=sma_200, mode='lines', name='SMA (200)', line=dict(color='navy')))
            indicator_values['SMA_200'] = {
                'current': sma_200.iloc[-1] if not sma_200.empty else None,
                'slope': (sma_200.iloc[-1] - sma_200.iloc[-20]) if len(sma_200) > 20 else None
            }
            
        elif indicator == "20-Day Bollinger Bands":
            bb_period = indicator_params.get('bb_period', 20)
            bb_std = indicator_params.get('bb_std', 2.0)
            sma = data['Close'].rolling(window=bb_period).mean()
            std = data['Close'].rolling(window=bb_period).std()
            bb_upper = sma + bb_std * std
            bb_lower = sma - bb_std * std
            bb_width = bb_upper - bb_lower
            
            fig.add_trace(go.Scatter(x=data.index, y=bb_upper, mode='lines', name='BB Upper', line=dict(color='red', dash='dash')))
            fig.add_trace(go.Scatter(x=data.index, y=bb_lower, mode='lines', name='BB Lower', line=dict(color='red', dash='dash')))
            fig.add_trace(go.Scatter(x=data.index, y=sma, mode='lines', name='BB Middle', line=dict(color='purple')))
            
            current_price = data['Close'].iloc[-1]
            bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) if not bb_upper.empty else None
            
            indicator_values['Bollinger_Bands'] = {
                'upper': bb_upper.iloc[-1] if not bb_upper.empty else None,
                'lower': bb_lower.iloc[-1] if not bb_lower.empty else None,
                'middle': sma.iloc[-1] if not sma.empty else None,
                'width': bb_width.iloc[-1] if not bb_width.empty else None,
                'position': bb_position,
                'squeeze': bb_width.iloc[-1] < bb_width.rolling(20).mean().iloc[-1] if len(bb_width) > 20 else None
            }
            
        elif indicator == "VWAP":
            data['VWAP'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
            fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], mode='lines', name='VWAP', line=dict(color='green')))
            indicator_values['VWAP'] = {
                'current': data['VWAP'].iloc[-1] if 'VWAP' in data.columns else None,
                'vs_price': data['Close'].iloc[-1] - data['VWAP'].iloc[-1] if 'VWAP' in data.columns else None
            }
            
        elif indicator == "RSI":
            rsi_period = indicator_params.get('rsi_period', 14)
            rsi = calculate_rsi(data['Close'], window=rsi_period)
            indicator_values['RSI'] = {
                'current': rsi.iloc[-1] if not rsi.empty else None,
                'previous': rsi.iloc[-2] if len(rsi) > 1 else None,
                'overbought': rsi.iloc[-1] > 70 if not rsi.empty else None,
                'oversold': rsi.iloc[-1] < 30 if not rsi.empty else None,
                'trend': 'rising' if len(rsi) > 5 and rsi.iloc[-1] > rsi.iloc[-5] else 'falling'
            }
            
        elif indicator == "MACD":
            fast = indicator_params.get('macd_fast', 12)
            slow = indicator_params.get('macd_slow', 26)
            macd_line, signal_line, histogram = calculate_macd(data['Close'], fast=fast, slow=slow)
            indicator_values['MACD'] = {
                'macd': macd_line.iloc[-1] if not macd_line.empty else None,
                'signal': signal_line.iloc[-1] if not signal_line.empty else None,
                'histogram': histogram.iloc[-1] if not histogram.empty else None,
                'crossover': (macd_line.iloc[-1] > signal_line.iloc[-1] and 
                            macd_line.iloc[-2] <= signal_line.iloc[-2]) if len(macd_line) > 1 else None,
                'divergence': macd_line.iloc[-1] - signal_line.iloc[-1] if not macd_line.empty else None
            }
            
        elif indicator == "Stochastic":
            k_percent, d_percent = calculate_stochastic(data['High'], data['Low'], data['Close'])
            indicator_values['Stochastic'] = {
                'k_percent': k_percent.iloc[-1] if not k_percent.empty else None,
                'd_percent': d_percent.iloc[-1] if not d_percent.empty else None,
                'overbought': k_percent.iloc[-1] > 80 if not k_percent.empty else None,
                'oversold': k_percent.iloc[-1] < 20 if not k_percent.empty else None,
                'crossover': (k_percent.iloc[-1] > d_percent.iloc[-1] and 
                            k_percent.iloc[-2] <= d_percent.iloc[-2]) if len(k_percent) > 1 else None
            }
            
        elif indicator == "ATR (Average True Range)":
            atr = calculate_atr(data['High'], data['Low'], data['Close'])
            current_atr = atr.iloc[-1] if not atr.empty else None
            avg_atr = atr.tail(20).mean() if len(atr) > 20 else current_atr
            indicator_values['ATR'] = {
                'current': current_atr,
                'average': avg_atr,
                'volatility': 'high' if current_atr and avg_atr and current_atr > avg_atr * 1.2 else 'low' if current_atr and avg_atr and current_atr < avg_atr * 0.8 else 'normal'
            }
            
        elif indicator == "Volume SMA":
            vol_sma = data['Volume'].rolling(window=20).mean()
            current_volume = data['Volume'].iloc[-1]
            vol_ratio = current_volume / vol_sma.iloc[-1] if not vol_sma.empty else None
            indicator_values['Volume_SMA'] = {
                'current_volume': current_volume,
                'average_volume': vol_sma.iloc[-1] if not vol_sma.empty else None,
                'volume_ratio': vol_ratio,
                'volume_trend': 'high' if vol_ratio and vol_ratio > 1.5 else 'low' if vol_ratio and vol_ratio < 0.5 else 'normal'
            }

    # Apply selected indicators
    for ind in indicators:
        add_indicator(ind)
        
    # Add RSI and MACD if not already selected (for comprehensive analysis)
    if "RSI" not in indicators:
        add_indicator("RSI")
    if "MACD" not in indicators:
        add_indicator("MACD")
        
    fig.update_layout(
        xaxis_rangeslider_visible=False, title=f"{ticker} Stock Chart with Technical Indicators",
        yaxis_title="Price", template="plotly_white", height=600
    )

    # Enhanced technical description for AI analysis
    last_close = data['Close'].iloc[-1]
    first_close = data['Close'].iloc[0]
    percent_change = ((last_close - first_close) / first_close) * 100
    direction = "upward" if percent_change > 0 else "downward"
    
    # Volume analysis
    recent_volume = data['Volume'].tail(5).mean()
    avg_volume = data['Volume'].mean()
    volume_trend = "above average" if recent_volume > avg_volume * 1.2 else "below average" if recent_volume < avg_volume * 0.8 else "normal"
    
    # Support and Resistance levels
    high_20 = data['High'].tail(20).max()
    low_20 = data['Low'].tail(20).min()
    
    # Create comprehensive technical description
    chart_description = f"""
    Comprehensive Technical Analysis for {ticker}:
    
    PRICE ACTION:
    - Current Price: ${last_close:.2f}
    - Price Trend: {direction} movement of {abs(percent_change):.2f}% over the period
    - 20-Day High: ${high_20:.2f}, 20-Day Low: ${low_20:.2f}
    - Volume: {volume_trend} ({recent_volume:,.0f} vs avg {avg_volume:,.0f})
    
    MOVING AVERAGES:"""
    
    if 'SMA_20' in indicator_values and indicator_values['SMA_20']['current']:
        sma_relation = "above" if last_close > indicator_values['SMA_20']['current'] else "below"
        sma_trend = "rising" if indicator_values['SMA_20']['slope'] and indicator_values['SMA_20']['slope'] > 0 else "falling"
        chart_description += f"""
    - 20-Day SMA: ${indicator_values['SMA_20']['current']:.2f} (Price is {sma_relation}, SMA is {sma_trend})"""
    
    if 'EMA_20' in indicator_values and indicator_values['EMA_20']['current']:
        ema_relation = "above" if last_close > indicator_values['EMA_20']['current'] else "below"
        ema_trend = "rising" if indicator_values['EMA_20']['slope'] and indicator_values['EMA_20']['slope'] > 0 else "falling"
        chart_description += f"""
    - 20-Day EMA: ${indicator_values['EMA_20']['current']:.2f} (Price is {ema_relation}, EMA is {ema_trend})"""
    
    if 'SMA_50' in indicator_values and indicator_values['SMA_50']['current']:
        sma50_relation = "above" if last_close > indicator_values['SMA_50']['current'] else "below"
        chart_description += f"""
    - 50-Day SMA: ${indicator_values['SMA_50']['current']:.2f} (Price is {sma50_relation})"""
        
    if 'SMA_200' in indicator_values and indicator_values['SMA_200']['current']:
        sma200_relation = "above" if last_close > indicator_values['SMA_200']['current'] else "below"
        chart_description += f"""
    - 200-Day SMA: ${indicator_values['SMA_200']['current']:.2f} (Price is {sma200_relation})"""
    
    chart_description += f"""
    
    BOLLINGER BANDS:"""
    if 'Bollinger_Bands' in indicator_values:
        bb = indicator_values['Bollinger_Bands']
        if bb['upper'] and bb['lower']:
            if bb['position']:
                if bb['position'] > 0.8:
                    bb_status = "near upper band (potentially overbought)"
                elif bb['position'] < 0.2:
                    bb_status = "near lower band (potentially oversold)"
                else:
                    bb_status = f"in middle zone (position: {bb['position']:.2f})"
            else:
                bb_status = "position unclear"
            
            squeeze_status = "in squeeze (low volatility)" if bb['squeeze'] else "normal width"
            chart_description += f"""
    - Upper: ${bb['upper']:.2f}, Lower: ${bb['lower']:.2f}, Middle: ${bb['middle']:.2f}
    - Price Position: {bb_status}
    - Band Status: {squeeze_status}"""
    
    chart_description += f"""
    
    MOMENTUM INDICATORS:"""
    if 'RSI' in indicator_values and indicator_values['RSI']['current']:
        rsi_val = indicator_values['RSI']['current']
        if rsi_val > 70:
            rsi_status = "overbought territory"
        elif rsi_val < 30:
            rsi_status = "oversold territory"
        else:
            rsi_status = "neutral zone"
        chart_description += f"""
    - RSI ({indicator_params.get('rsi_period', 14)}): {rsi_val:.1f} ({rsi_status})"""
    
    if 'MACD' in indicator_values:
        macd = indicator_values['MACD']
        if macd['macd'] and macd['signal']:
            macd_signal = "bullish" if macd['macd'] > macd['signal'] else "bearish"
            crossover_text = "recent bullish crossover detected" if macd['crossover'] else "no recent crossover"
            chart_description += f"""
    - MACD: {macd['macd']:.3f}, Signal: {macd['signal']:.3f} ({macd_signal} - {crossover_text})"""
    
    if 'Stochastic' in indicator_values:
        stoch = indicator_values['Stochastic']
        if stoch['k_percent']:
            stoch_status = "overbought" if stoch['overbought'] else "oversold" if stoch['oversold'] else "neutral"
            chart_description += f"""
    - Stochastic %K: {stoch['k_percent']:.1f}, %D: {stoch['d_percent']:.1f} ({stoch_status})"""
    
    if 'VWAP' in indicator_values and indicator_values['VWAP']['current']:
        vwap_relation = "above" if indicator_values['VWAP']['vs_price'] > 0 else "below"
        chart_description += f"""
    
    VOLUME INDICATORS:
    - VWAP: ${indicator_values['VWAP']['current']:.2f} (Price is {vwap_relation} VWAP by ${abs(indicator_values['VWAP']['vs_price']):.2f})"""
    
    if 'ATR' in indicator_values:
        atr = indicator_values['ATR']
        chart_description += f"""
    - ATR: {atr['current']:.2f} (Volatility is {atr['volatility']})"""
    
    chart_description += f"""
    
    SELECTED INDICATORS: {', '.join(indicators)}
    """
    
    # AI Analysis with comprehensive data
    try:
        contents = [{"role": "user", "parts": [f"""
            You are an Expert Technical Analyst at a premier trading firm. Analyze this stock data comprehensively:
            
            {chart_description}
            
            ANALYSIS REQUIREMENTS:
            1. Evaluate ALL provided technical indicators and their signals
            2. Identify any confluences (multiple indicators agreeing)
            3. Note any divergences between price and indicators
            4. Consider the overall market structure (support/resistance, trend)
            5. Assess momentum and volatility conditions
            6. Provide specific entry/exit levels if applicable
            
            Based on this comprehensive technical analysis, provide your recommendation:
            'Strong Buy', 'Buy', 'Weak Buy', 'Hold', 'Weak Sell', 'Sell', or 'Strong Sell'
            
            Return as JSON with keys: 'action' and 'justification'
            The justification should reference specific indicator values and explain your reasoning.
        """]}]

        response = gen_model.generate_content(contents=contents)
        result_text = response.text
        
        json_start_index = result_text.find('{')
        json_end_index = result_text.rfind('}') + 1
        
        if json_start_index != -1 and json_end_index > json_start_index:
            json_string = result_text[json_start_index:json_end_index]
            result = json.loads(json_string)
        else:
            raise ValueError("No valid JSON object found in the response")

    except Exception as e:
        result = {"action": "Error", "justification": f"Enhanced analysis error: {e}"}

    return fig, result

# Additional function to get trading signals summary
def get_trading_signals_summary(indicator_values, current_price):
    """Generate a summary of all trading signals"""
    signals = {"bullish": 0, "bearish": 0, "neutral": 0}
    signal_details = []
    
    # SMA Signal
    if 'SMA_20' in indicator_values and indicator_values['SMA_20']['current']:
        if current_price > indicator_values['SMA_20']['current']:
            signals["bullish"] += 1
            signal_details.append("Price above SMA (Bullish)")
        else:
            signals["bearish"] += 1
            signal_details.append("Price below SMA (Bearish)")
    
    # RSI Signal
    if 'RSI' in indicator_values and indicator_values['RSI']['current']:
        rsi = indicator_values['RSI']['current']
        if rsi > 70:
            signals["bearish"] += 1
            signal_details.append(f"RSI Overbought {rsi:.1f} (Bearish)")
        elif rsi < 30:
            signals["bullish"] += 1
            signal_details.append(f"RSI Oversold {rsi:.1f} (Bullish)")
        else:
            signals["neutral"] += 1
            signal_details.append(f"RSI Neutral {rsi:.1f}")
    
    # MACD Signal
    if 'MACD' in indicator_values:
        macd = indicator_values['MACD']
        if macd['macd'] and macd['signal']:
            if macd['macd'] > macd['signal']:
                signals["bullish"] += 1
                signal_details.append("MACD Above Signal (Bullish)")
            else:
                signals["bearish"] += 1
                signal_details.append("MACD Below Signal (Bearish)")
    
    # Bollinger Bands Signal
    if 'Bollinger_Bands' in indicator_values:
        bb = indicator_values['Bollinger_Bands']
        if bb['position']:
            if bb['position'] > 0.8:
                signals["bearish"] += 1
                signal_details.append("Near BB Upper Band (Bearish)")
            elif bb['position'] < 0.2:
                signals["bullish"] += 1
                signal_details.append("Near BB Lower Band (Bullish)")
            else:
                signals["neutral"] += 1
                signal_details.append("BB Middle Zone (Neutral)")
    
    return signals, signal_details