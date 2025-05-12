# analysis.py - Technical analysis and combined analysis functions

import streamlit as st
import plotly.graph_objects as go
import tempfile
import os
import json
from config import gen_model

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

    # Save chart as temporary PNG file and read image bytes
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
        fig.write_image(tmpfile.name)
        tmpfile_path = tmpfile.name
        
    with open(tmpfile_path, "rb") as f:
        image_bytes = f.read()
        
    os.remove(tmpfile_path)

    # Create an image Part
    image_part = {
        "data": image_bytes,  
        "mime_type": "image/png"
    }

    # Updated prompt asking for a detailed justification of technical analysis and a recommendation.
    analysis_prompt = (
        f"You are a Stock Trader specializing in Technical Analysis at a top financial institution. "
        f"Analyze the stock chart for {ticker} based on its candlestick chart and the displayed technical indicators. "
        f"Provide a detailed justification of your analysis, explaining what patterns, signals, and trends you observe. "
        f"Then, based solely on the chart, provide a recommendation from the following options: "
        f"'Strong Buy', 'Buy', 'Weak Buy', 'Hold', 'Weak Sell', 'Sell', or 'Strong Sell'. "
        f"Return your output as a JSON object with two keys: 'action' and 'justification'."
    )

    # Call the Gemini API with text and image input
    try:
        contents = [
            {"role": "user", "parts": [analysis_prompt]},
            {"role": "user", "parts": [image_part]}
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