# market_risk_analysis.py - Comprehensive Market Risk & Macro Analysis
import streamlit as st
import requests
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from config import ALPHA_VANTAGE_API_KEY, gen_model

# Sector mapping for stocks
SECTOR_MAPPING = {
    'AAPL': {'sector': 'Technology', 'etf': 'XLK', 'beta_typical': 1.2},
    'MSFT': {'sector': 'Technology', 'etf': 'XLK', 'beta_typical': 0.9},
    'GOOG': {'sector': 'Technology', 'etf': 'XLK', 'beta_typical': 1.1},
    'GOOGL': {'sector': 'Technology', 'etf': 'XLK', 'beta_typical': 1.1},
    'AMZN': {'sector': 'Consumer Discretionary', 'etf': 'XLY', 'beta_typical': 1.3},
    'TSLA': {'sector': 'Consumer Discretionary', 'etf': 'XLY', 'beta_typical': 2.0},
    'META': {'sector': 'Technology', 'etf': 'XLK', 'beta_typical': 1.4},
    'NVDA': {'sector': 'Technology', 'etf': 'XLK', 'beta_typical': 1.8},
    'JPM': {'sector': 'Financial', 'etf': 'XLF', 'beta_typical': 1.1},
    'V': {'sector': 'Financial', 'etf': 'XLF', 'beta_typical': 0.8},
    'JNJ': {'sector': 'Healthcare', 'etf': 'XLV', 'beta_typical': 0.7},
    'PG': {'sector': 'Consumer Staples', 'etf': 'XLP', 'beta_typical': 0.5},
    'WMT': {'sector': 'Consumer Staples', 'etf': 'XLP', 'beta_typical': 0.6}
}

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_market_data():
    """Get market risk indicators from Yahoo Finance"""
    try:
        # Market indicators
        vix = yf.download("^VIX", period="5d", interval="1d")
        spy = yf.download("SPY", period="1mo", interval="1d")
        treasury_10y = yf.download("^TNX", period="5d", interval="1d")
        treasury_3m = yf.download("^IRX", period="5d", interval="1d")
        dxy = yf.download("DX-Y.NYB", period="5d", interval="1d")
        
        market_data = {
            'vix_current': float(vix['Close'].iloc[-1]) if not vix.empty else 20.0,
            'vix_change': float(((vix['Close'].iloc[-1] - vix['Close'].iloc[-2]) / vix['Close'].iloc[-2] * 100)) if len(vix) > 1 else 0.0,
            'spy_performance': float(((spy['Close'].iloc[-1] - spy['Close'].iloc[-5]) / spy['Close'].iloc[-5] * 100)) if len(spy) > 5 else 0.0,
            'treasury_10y': float(treasury_10y['Close'].iloc[-1]) if not treasury_10y.empty else 4.5,
            'treasury_3m': float(treasury_3m['Close'].iloc[-1]) if not treasury_3m.empty else 4.0,
            'dxy_current': float(dxy['Close'].iloc[-1]) if not dxy.empty else 100.0
        }
        
        return market_data
    except Exception as e:
        # Return default values if API fails
        return {
            'vix_current': 20.0, 'vix_change': 0.0, 'spy_performance': 0.0,
            'treasury_10y': 4.5, 'treasury_3m': 4.0, 'dxy_current': 100.0
        }

@st.cache_data(ttl=1800)
def get_sector_data(ticker):
    """Get sector-specific risk data"""
    try:
        sector_info = SECTOR_MAPPING.get(ticker, {'sector': 'Unknown', 'etf': 'SPY', 'beta_typical': 1.0})
        sector_etf = sector_info['etf']
        
        # Get sector ETF data
        etf_data = yf.download(sector_etf, period="1mo", interval="1d")
        spy_data = yf.download("SPY", period="1mo", interval="1d")
        
        if not etf_data.empty and not spy_data.empty:
            # Calculate sector vs market performance - ensure single values
            etf_return = float(((etf_data['Close'].iloc[-1] - etf_data['Close'].iloc[-5]) / etf_data['Close'].iloc[-5] * 100))
            spy_return = float(((spy_data['Close'].iloc[-1] - spy_data['Close'].iloc[-5]) / spy_data['Close'].iloc[-5] * 100))
            sector_vs_market = etf_return - spy_return
            
            # Calculate sector volatility - ensure single value
            etf_returns = etf_data['Close'].pct_change().dropna()
            sector_volatility = float(etf_returns.std() * np.sqrt(252) * 100)  # Annualized volatility
            
            return {
                'sector': sector_info['sector'],
                'sector_performance': etf_return,
                'sector_vs_market': sector_vs_market,
                'sector_volatility': sector_volatility,
                'beta_typical': float(sector_info['beta_typical'])
            }
        else:
            return {
                'sector': sector_info['sector'], 'sector_performance': 0.0,
                'sector_vs_market': 0.0, 'sector_volatility': 20.0, 
                'beta_typical': float(sector_info['beta_typical'])
            }
    except Exception:
        return {
            'sector': 'Unknown', 'sector_performance': 0.0, 'sector_vs_market': 0.0,
            'sector_volatility': 20.0, 'beta_typical': 1.0
        }

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_economic_indicators():
    """Get economic indicators from Alpha Vantage and FRED"""
    economic_data = {}
    
    # Try Alpha Vantage economic indicators
    try:
        # GDP
        gdp_url = f"https://www.alphavantage.co/query?function=REAL_GDP&interval=annual&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(gdp_url, timeout=10)
        if response.status_code == 200:
            gdp_data = response.json()
            if 'data' in gdp_data and len(gdp_data['data']) > 1:
                recent_gdp = float(gdp_data['data'][0]['value'])
                prev_gdp = float(gdp_data['data'][1]['value'])
                economic_data['gdp_growth'] = ((recent_gdp - prev_gdp) / prev_gdp) * 100
    except Exception:
        economic_data['gdp_growth'] = 2.5  # Default
    
    # Try more economic indicators
    try:
        # Inflation
        inflation_url = f"https://www.alphavantage.co/query?function=INFLATION&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(inflation_url, timeout=10)
        if response.status_code == 200:
            inflation_data = response.json()
            if 'data' in inflation_data and len(inflation_data['data']) > 0:
                economic_data['inflation_rate'] = float(inflation_data['data'][0]['value'])
    except Exception:
        economic_data['inflation_rate'] = 3.2  # Default
    
    # Fill in defaults for missing data
    economic_data.setdefault('gdp_growth', 2.5)
    economic_data.setdefault('inflation_rate', 3.2)
    economic_data.setdefault('unemployment_rate', 3.8)
    economic_data.setdefault('consumer_confidence', 102)
    
    return economic_data

def calculate_stock_beta(ticker, market_data):
    """Calculate stock beta vs market"""
    try:
        # Get stock and market data
        stock_data = yf.download(ticker, period="1y", interval="1d")
        market_data = yf.download("SPY", period="1y", interval="1d")
        
        if len(stock_data) > 50 and len(market_data) > 50:
            # Calculate returns
            stock_returns = stock_data['Close'].pct_change().dropna()
            market_returns = market_data['Close'].pct_change().dropna()
            
            # Align dates
            common_dates = stock_returns.index.intersection(market_returns.index)
            if len(common_dates) > 50:
                stock_aligned = stock_returns.loc[common_dates]
                market_aligned = market_returns.loc[common_dates]
                
                # Calculate beta
                covariance = np.cov(stock_aligned, market_aligned)[0][1]
                market_variance = np.var(market_aligned)
                beta = covariance / market_variance if market_variance != 0 else 1.0
                
                return beta
    except Exception:
        pass
    
    # Return typical beta for sector if calculation fails
    return SECTOR_MAPPING.get(ticker, {'beta_typical': 1.0})['beta_typical']

def analyze_market_environment(market_data, economic_data):
    """Analyze overall market environment"""
    risk_score = 50  # Start neutral
    environment_factors = []
    
    # VIX Analysis - ensure we get a single value
    vix = float(market_data['vix_current'])
    if vix < 15:
        risk_score -= 15
        environment_factors.append("Low volatility environment (VIX < 15)")
    elif vix < 25:
        risk_score -= 5
        environment_factors.append("Normal volatility environment")
    elif vix < 35:
        risk_score += 15
        environment_factors.append("Elevated volatility (VIX > 25)")
    else:
        risk_score += 25
        environment_factors.append("High fear environment (VIX > 35)")
    
    # Interest Rate Analysis - ensure single value
    treasury_10y = float(market_data['treasury_10y'])
    if treasury_10y > 5:
        risk_score += 10
        environment_factors.append("High interest rates pressuring valuations")
    elif treasury_10y < 3:
        risk_score -= 5
        environment_factors.append("Low interest rates supportive")
    
    # Economic Growth - ensure single value
    gdp_growth = float(economic_data['gdp_growth'])
    if gdp_growth > 3:
        risk_score -= 10
        environment_factors.append("Strong economic growth")
    elif gdp_growth < 1:
        risk_score += 15
        environment_factors.append("Weak economic growth")
    
    # Inflation Impact - ensure single value
    inflation = float(economic_data['inflation_rate'])
    if inflation > 4:
        risk_score += 10
        environment_factors.append("High inflation pressuring margins")
    elif inflation < 2:
        risk_score += 5
        environment_factors.append("Low inflation, potential deflation risk")
    
    # Market Performance - ensure single value
    spy_perf = float(market_data['spy_performance'])
    if spy_perf < -5:
        risk_score += 10
        environment_factors.append("Market in downtrend")
    elif spy_perf > 5:
        risk_score -= 5
        environment_factors.append("Market momentum positive")
    
    # Normalize score
    risk_score = max(0, min(100, risk_score))
    
    return risk_score, environment_factors

def get_stock_specific_risks(ticker, investing_type, market_data, sector_data, economic_data):
    """Analyze stock-specific risks based on macro environment"""
    risks = []
    
    # Convert to float values to avoid Series issues
    treasury_10y = float(market_data['treasury_10y'])
    gdp_growth = float(economic_data['gdp_growth'])
    inflation_rate = float(economic_data['inflation_rate'])
    unemployment_rate = float(economic_data.get('unemployment_rate', 4.0))
    vix_current = float(market_data['vix_current'])
    beta = float(sector_data['beta_typical'])
    
    # Sector-specific risks
    sector = sector_data['sector']
    if sector == 'Technology':
        if treasury_10y > 4.5:
            risks.append("Tech stocks sensitive to rising interest rates")
        if gdp_growth < 2:
            risks.append("Tech growth may slow in weak economy")
    elif sector == 'Financial':
        if treasury_10y < 3:
            risks.append("Low rates pressure bank margins")
        if gdp_growth < 1.5:
            risks.append("Economic weakness increases loan defaults")
    elif sector == 'Consumer Discretionary':
        if inflation_rate > 4:
            risks.append("High inflation reduces consumer spending")
        if unemployment_rate > 5:
            risks.append("High unemployment hurts discretionary spending")
    elif sector == 'Healthcare':
        risks.append("Defensive sector, lower growth in bull markets")
    elif sector == 'Consumer Staples':
        if inflation_rate > 4:
            risks.append("Rising costs may pressure margins")
    
    # Beta-based risks
    if beta > 1.5:
        risks.append(f"High beta ({beta:.1f}) amplifies market volatility")
    elif beta < 0.7:
        risks.append(f"Low beta ({beta:.1f}) may underperform in bull markets")
    
    # VIX-based risks
    if vix_current > 30 and beta > 1.2:
        risks.append("High volatility environment particularly risky for high-beta stock")
    
    # Strategy-specific risks
    if investing_type == 'Growth Investing':
        if treasury_10y > 5:
            risks.append("Rising rates challenge growth stock valuations")
    elif investing_type == 'Value Investing':
        if gdp_growth < 1:
            risks.append("Economic weakness may keep value stocks depressed")
    
    return risks

def calculate_market_risk_score(market_data, sector_data, economic_data, ticker, investing_type):
    """Calculate comprehensive market risk score"""
    
    # Get base market environment score
    base_score, _ = analyze_market_environment(market_data, economic_data)
    
    # Adjust for sector performance - ensure single values
    sector_adjustment = 0
    sector_vs_market = float(sector_data['sector_vs_market']) if sector_data['sector_vs_market'] is not None else 0.0
    if sector_vs_market < -5:
        sector_adjustment += 10  # Sector underperforming
    elif sector_vs_market > 5:
        sector_adjustment -= 5   # Sector outperforming
    
    # Adjust for stock beta - ensure single value
    beta = float(sector_data['beta_typical']) if sector_data['beta_typical'] is not None else 1.0
    beta_adjustment = 0
    vix_current = float(market_data['vix_current'])
    if vix_current > 25:  # High volatility environment
        if beta > 1.5:
            beta_adjustment += 15
        elif beta > 1.2:
            beta_adjustment += 10
        elif beta < 0.8:
            beta_adjustment -= 5
    
    # Strategy-specific adjustments
    strategy_adjustment = 0
    gdp_growth = float(economic_data['gdp_growth'])
    if investing_type == 'Swing Trading':
        if vix_current > 30:
            strategy_adjustment += 10  # High vol bad for swing trading
    elif investing_type == 'Value Investing':
        if gdp_growth < 1.5:
            strategy_adjustment += 5   # Weak economy challenges value
    
    final_score = base_score + sector_adjustment + beta_adjustment + strategy_adjustment
    final_score = max(0, min(100, final_score))
    
    return final_score

@st.cache_data(ttl=1800)
def analyze_market_risk_macro(ticker, investing_type, use_demo=False):
    """Main function for market risk and macro analysis"""
    
    if use_demo:
        # Generate realistic demo data
        np.random.seed(hash(ticker) % 10000)
        market_data = {
            'vix_current': np.random.uniform(15, 35),
            'vix_change': np.random.uniform(-15, 15),
            'spy_performance': np.random.uniform(-5, 8),
            'treasury_10y': np.random.uniform(3.5, 5.5),
            'treasury_3m': np.random.uniform(3.0, 5.0),
            'dxy_current': np.random.uniform(95, 110)
        }
        economic_data = {
            'gdp_growth': np.random.uniform(1.0, 4.0),
            'inflation_rate': np.random.uniform(2.0, 5.0),
            'unemployment_rate': np.random.uniform(3.0, 6.0),
            'consumer_confidence': np.random.uniform(85, 120)
        }
        sector_data = get_sector_data(ticker)  # This can work even in demo mode
    else:
        # Get real data
        market_data = get_market_data()
        economic_data = get_economic_indicators()
        sector_data = get_sector_data(ticker)
    
    # Calculate comprehensive risk score
    risk_score = calculate_market_risk_score(market_data, sector_data, economic_data, ticker, investing_type)
    
    # Determine market environment
    if risk_score < 30:
        environment = "Low Risk"
        env_color = "lightgreen"
    elif risk_score < 60:
        environment = "Normal Risk"
        env_color = "gold"
    else:
        environment = "High Risk"
        env_color = "salmon"
    
    # Get risk factors
    _, market_factors = analyze_market_environment(market_data, economic_data)
    stock_risks = get_stock_specific_risks(ticker, investing_type, market_data, sector_data, economic_data)
    
    # Compile key risk factors
    key_risk_factors = []
    
    # Market Risk Content
    key_risk_factors.append(f"**Market Risk:** VIX at {market_data['vix_current']:.1f} ({'High Fear' if market_data['vix_current'] > 30 else 'Normal' if market_data['vix_current'] > 20 else 'Low Fear'})")
    key_risk_factors.append(f"**Interest Rates:** 10Y Treasury at {market_data['treasury_10y']:.2f}% ({'Pressuring Valuations' if market_data['treasury_10y'] > 5 else 'Supportive' if market_data['treasury_10y'] < 3.5 else 'Neutral'})")
    if sector_data['sector_vs_market'] != 0:
        sector_status = "outperforming" if sector_data['sector_vs_market'] > 0 else "underperforming"
        key_risk_factors.append(f"**Sector Risk:** {sector_data['sector']} sector {sector_status} market by {abs(sector_data['sector_vs_market']):.1f}%")
    
    # Macro Analysis Points
    key_risk_factors.append(f"**Economic Growth:** GDP growing at {economic_data['gdp_growth']:.1f}% ({'Strong' if economic_data['gdp_growth'] > 3 else 'Weak' if economic_data['gdp_growth'] < 2 else 'Moderate'})")
    key_risk_factors.append(f"**Inflation Impact:** CPI at {economic_data['inflation_rate']:.1f}% ({'High Pressure' if economic_data['inflation_rate'] > 4 else 'Low Risk' if economic_data['inflation_rate'] < 2.5 else 'Moderate'})")
    
    # Stock-Specific Risk Points
    key_risk_factors.extend([f"**Stock-Specific:** {risk}" for risk in stock_risks[:3]])  # Limit to top 3
    
    return {
        'risk_score': int(risk_score),
        'environment': environment,
        'env_color': env_color,
        'key_risk_factors': key_risk_factors,
        'market_data': market_data,
        'economic_data': economic_data,
        'sector_data': sector_data,
        'investing_type': investing_type,
        'data_source': 'Demo Data' if use_demo else 'Real Market Data'
    }