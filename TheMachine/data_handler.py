# data_handler.py - Data fetching and processing
import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime, timedelta
from alpha_vantage.timeseries import TimeSeries
from config import ALPHA_VANTAGE_API_KEY

@st.cache_data(ttl=3600)
def download_stock_data(ticker, start_date, end_date, max_retries=3):
    """Download stock data from Alpha Vantage API"""
    start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
    end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else end_date
    
    ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
    
    for retry in range(max_retries):
        try:
            data, meta_data = ts.get_daily(symbol=ticker, outputsize='full')
            
            data = data.rename(columns={
                '1. open': 'Open', '2. high': 'High', '3. low': 'Low',
                '4. close': 'Close', '5. volume': 'Volume'
            })
            
            data = data.sort_index().loc[start_str:end_str]
            
            if not data.empty:
                return data
            else:
                return pd.DataFrame()
                
        except Exception as e:
            error_str = str(e)
            if "Alpha Vantage API limit" in error_str or "Error getting data" in error_str:
                if retry < max_retries - 1:
                    wait_time = 1 + (2 ** retry) + random.uniform(0, 2)
                    time.sleep(wait_time)
                else:
                    return pd.DataFrame()
            else:
                return pd.DataFrame()
    
    return pd.DataFrame()

def create_demo_data(ticker, days=365):
    """Create synthetic demo data for testing"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')
    
    base_prices = {
        'AAPL': 150, 'MSFT': 300, 'GOOG': 2500, 'AMZN': 3000, 'META': 250,
        'TSLA': 200, 'NVDA': 400, 'JPM': 130, 'V': 200, 'JNJ': 160
    }
    base_price = base_prices.get(ticker, 100)
    
    np.random.seed(hash(ticker) % 10000)
    returns = np.random.normal(0.0005, 0.015, len(date_range))
    cum_returns = np.cumprod(1 + returns)
    
    close_prices = base_price * cum_returns
    daily_volatility = 0.015 * close_prices
    
    high_prices = close_prices + np.random.normal(0.5, 0.5, len(close_prices)) * daily_volatility
    low_prices = close_prices - np.random.normal(0.5, 0.5, len(close_prices)) * daily_volatility
    open_prices = low_prices + (high_prices - low_prices) * np.random.random(len(close_prices))
    
    for i in range(len(close_prices)):
        max_price = max(high_prices[i], close_prices[i], open_prices[i])
        min_price = min(low_prices[i], close_prices[i], open_prices[i])
        high_prices[i] = max_price
        low_prices[i] = min_price
    
    volume = np.abs(returns) * np.random.normal(1e7, 5e6, len(returns))
    
    return pd.DataFrame({
        'Open': open_prices, 'High': high_prices, 'Low': low_prices,
        'Close': close_prices, 'Volume': volume.astype(int)
    }, index=date_range)