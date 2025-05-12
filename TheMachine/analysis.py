# analysis.py - Technical analysis and combined analysis functions

import streamlit as st
import plotly.graph_objects as go
import json
from config import gen_model
import base64
from io import BytesIO

def analyze_ticker(ticker, data, indicators):
    """
    Analyze a stock ticker using technical indicators and AI
    
    Args:
        ticker: The stock ticker symbol
        data: DataFrame with OHLC data
        indicators: List of technical indicators to display
        
    Returns:
        fig: Plotly figure object
        result: AI analysis result as a dictionary
    """
    # Build candlestick chart for the given ticker's data
    fig = go.Figure(data=[
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Candlestick"
        )
    ])

    # Add selected technical indicators
    def add_indicator(indicator):
        if indicator == "20-Day SMA":
            sma = data['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(x=data.index, y=sma, mode='lines', name='SMA (20)'))
        elif indicator == "20-Day EMA":
            ema = data['Close'].ewm(span=20).mean()
            fig.add_trace(go.Scatter(x=data.index, y=ema, mode='lines', name='EMA (20)'))
        elif indicator == "20-Day Bollinger Bands":
            sma = data['Close'].rolling(window=20).mean()
            std = data['Close'].rolling(window=20).std()
            bb_upper = sma + 2 * std
            bb_lower = sma - 2 * std
            fig.add_trace(go.Scatter(x=data.index, y=bb_upper, mode='lines', name='BB Upper'))
            fig.add_trace(go.Scatter(x=data.index, y=bb_lower, mode='lines', name='BB Lower'))
        elif indicator == "VWAP":
            data['VWAP'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
            fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], mode='lines', name='VWAP'))
            
    for ind in indicators:
        add_indicator(ind)
        
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        title=f"{ticker} Stock Chart",
        yaxis_title="Price",
        template="plotly_white",
        height=600
    )

    # For cloud deployment, use a descriptive analysis instead of image processing
    # Create a text description of the chart for AI analysis
    last_close = data['Close'].iloc[-1]
    first_close = data['Close'].iloc[0]
    percent_change = ((last_close - first_close) / first_close) * 100
    direction = "upward" if percent_change > 0 else "downward"
    
    # Sample technical indicators for analysis
    if len(data) >= 20:
        sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
        above_sma = last_close > sma_20
        sma_status = "above" if above_sma else "below"
    else:
        sma_status = "unknown (insufficient data)"
    
    # Create chart description for AI
    chart_description = f"""
    Technical analysis for {ticker}:
    - Price trend: {direction} movement of {abs(percent_change):.2f}% over the period
    - Current price (${last_close:.2f}) is {sma_status} the 20-day SMA
    - Starting price: ${first_close:.2f}, Ending price: ${last_close:.2f}
    - Highest price in period: ${data['High'].max():.2f}
    - Lowest price in period: ${data['Low'].min():.2f}
    - Volume trend: {'increasing' if data['Volume'].iloc[-1] > data['Volume'].iloc[0] else 'decreasing'}
    - Selected indicators: {', '.join(indicators)}
    """
    
    # Call the Gemini API with text input instead of image
    try:
        contents = [
            {"role": "user", "parts": [f"""
                You are a Stock Trader specializing in Technical Analysis at a top financial institution. 
                Analyze the stock data for {ticker} based on the following information:
                
                {chart_description}
                
                Provide a detailed justification of your analysis, explaining what patterns, signals, and trends you observe.
                Then, based solely on this technical data, provide a recommendation from the following options:
                'Strong Buy', 'Buy', 'Weak Buy', 'Hold', 'Weak Sell', 'Sell', or 'Strong Sell'.
                
                Return your output as a JSON object with two keys: 'action' and 'justification'.
            """]}
        ]

        response = gen_model.generate_content(
            contents=contents
        )

        # Attempt to parse JSON from the response text
        result_text = response.text
        # Find the start and end of the JSON object within the text (if Gemini includes extra text)
        json_start_index = result_text.find('{')
        json_end_index = result_text.rfind('}') + 1  # +1 to include the closing brace
        
        if json_start_index != -1 and json_end_index > json_start_index:
            json_string = result_text[json_start_index:json_end_index]
            result = json.loads(json_string)
        else:
            raise ValueError("No valid JSON object found in the response")

    except json.JSONDecodeError as e:
        result = {"action": "Error", "justification": f"JSON Parsing error: {e}. Raw response text: {response.text if 'response' in locals() else 'No response generated'}"}
    except ValueError as ve:
        result = {"action": "Error", "justification": f"Value Error: {ve}. Raw response text: {response.text if 'response' in locals() else 'No response generated'}"}
    except Exception as e:
        result = {"action": "Error", "justification": f"General Error: {e}"}

    return fig, result
