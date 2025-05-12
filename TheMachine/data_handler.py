# data_handler.py - Functions for fetching and processing stock data

import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime, timedelta
from alpha_vantage.timeseries import TimeSeries
from config import ALPHA_VANTAGE_API_KEY

@st.cache_data(ttl=3600)  # Cache data for 1 hour to reduce API calls
def download_stock_data(ticker, start_date, end_date, max_retries=3):
    """Download stock data from Alpha Vantage API using the official library"""
    # Convert dates to string format
    start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
    end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else end_date
    
    # Initialize TimeSeries object
    ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
    
    for retry in range(max_retries):
        try:
            # Get daily data with full output size to ensure we have enough historical data
            data, meta_data = ts.get_daily(symbol=ticker, outputsize='full')
            
            # Rename columns to match expected format
            data = data.rename(columns={
                '1. open': 'Open',
                '2. high': 'High',
                '3. low': 'Low',
                '4. close': 'Close',
                '5. volume': 'Volume'
            })
            
            # Alpha Vantage returns data in reverse chronological order with most recent first
            # Sort to ensure chronological order (oldest first)
            data = data.sort_index()
            
            # Filter to date range
            data = data.loc[start_str:end_str]
            
            # If we have data, return it
            if not data.empty:
                return data
            else:
                # If empty after filtering, the date range might be invalid
                return pd.DataFrame()
                
        except Exception as e:
            error_str = str(e)
            # Check if we hit rate limit
            if "Alpha Vantage API limit" in error_str or "Error getting data" in error_str:
                if retry < max_retries - 1:
                    # Wait longer between retries (Alpha Vantage free tier allows 5 calls per minute)
                    wait_time = 1 + (2 ** retry) + random.uniform(0, 2)
                    time.sleep(wait_time)
                else:
                    # Last retry failed, return empty DataFrame
                    return pd.DataFrame()
            else:
                # Other error (not rate limit related)
                return pd.DataFrame()
    
    # If all retries failed, return empty DataFrame
    return pd.DataFrame()

def create_demo_data(ticker, days=365):
    """Create synthetic demo data for testing when API fails"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
    
    # Start with a base price that looks realistic for the ticker
    base_prices = {
        'AAPL': 150, 'MSFT': 300, 'GOOG': 2500, 'AMZN': 3000, 'META': 250,
        'TSLA': 200, 'NVDA': 400, 'JPM': 130, 'V': 200, 'JNJ': 160
    }
    base_price = base_prices.get(ticker, 100)  # Default to 100 if ticker not in our map
    
    # Generate realistic looking price movements
    np.random.seed(hash(ticker) % 10000)  # Seed based on ticker for consistency
    
    # Daily returns with slight positive drift
    returns = np.random.normal(0.0005, 0.015, len(date_range))
    
    # Cumulative returns
    cum_returns = np.cumprod(1 + returns)
    
    # Generate OHLC data
    close_prices = base_price * cum_returns
    daily_volatility = 0.015 * close_prices
    
    high_prices = close_prices + np.random.normal(0.5, 0.5, len(close_prices)) * daily_volatility
    low_prices = close_prices - np.random.normal(0.5, 0.5, len(close_prices)) * daily_volatility
    open_prices = low_prices + (high_prices - low_prices) * np.random.random(len(close_prices))
    
    # Ensure OHLC relationship: low <= open, close <= high
    for i in range(len(close_prices)):
        max_price = max(high_prices[i], close_prices[i], open_prices[i])
        min_price = min(low_prices[i], close_prices[i], open_prices[i])
        high_prices[i] = max_price
        low_prices[i] = min_price
    
    # Generate volume data - higher for volatile days
    volume = np.abs(returns) * np.random.normal(1e7, 5e6, len(returns))
    
    # Create DataFrame
    data = pd.DataFrame({
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Volume': volume.astype(int)
    }, index=date_range)
    
    return data