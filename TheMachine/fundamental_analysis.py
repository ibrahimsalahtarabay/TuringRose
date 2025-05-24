# fundamental_analysis.py - Fundamental analysis
import streamlit as st
import requests
import json
import random
from config import ALPHA_VANTAGE_API_KEY, gen_model

@st.cache_data(ttl=3600)
def get_company_overview(ticker):
    """Get company overview data from Alpha Vantage"""
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'Symbol' in data:
                return data
            else:
                st.warning(f"No fundamental data available for {ticker}")
                return None
        else:
            st.warning(f"Error fetching fundamental data: Status {response.status_code}")
            return None
    except Exception as e:
        st.warning(f"Error fetching fundamental data: {e}")
        return None

def generate_demo_fundamental_data(ticker):
    """Generate demo fundamental data when API fails"""
    random.seed(hash(ticker) % 10000)
    
    base_values = {
        'AAPL': {'market_cap': 3000000, 'pe': 25, 'revenue_growth': 5},
        'MSFT': {'market_cap': 2800000, 'pe': 28, 'revenue_growth': 8},
        'GOOG': {'market_cap': 1800000, 'pe': 22, 'revenue_growth': 12},
    }
    
    base = base_values.get(ticker, {'market_cap': 500000, 'pe': 20, 'revenue_growth': 5})
    
    return {
        'MarketCapitalization': str(base['market_cap'] * random.uniform(0.8, 1.2)),
        'PERatio': str(base['pe'] * random.uniform(0.7, 1.3)),
        'PriceToBookRatio': str(random.uniform(1.5, 4.0)),
        'ROE': str(random.uniform(10, 25)),
        'CurrentRatio': str(random.uniform(1.0, 2.5)),
        'DebtToEquityRatio': str(random.uniform(0.2, 1.5)),
        'RevenuePerShareTTM': str(random.uniform(10, 50)),
        'EPS': str(random.uniform(2, 15)),
        'DividendYield': str(random.uniform(0, 3)),
        'profitMargin': str(random.uniform(5, 25)),
    }

def calculate_fundamental_score(overview_data):
    """Calculate fundamental score using Gemini AI"""
    fundamental_summary = f"""
    Company Fundamental Data:
    Market Cap: ${overview_data.get('MarketCapitalization', 'N/A')}
    P/E Ratio: {overview_data.get('PERatio', 'N/A')}
    P/B Ratio: {overview_data.get('PriceToBookRatio', 'N/A')}
    ROE: {overview_data.get('ROE', 'N/A')}%
    Current Ratio: {overview_data.get('CurrentRatio', 'N/A')}
    Debt-to-Equity: {overview_data.get('DebtToEquityRatio', 'N/A')}
    Revenue Per Share: ${overview_data.get('RevenuePerShareTTM', 'N/A')}
    EPS: ${overview_data.get('EPS', 'N/A')}
    Dividend Yield: {overview_data.get('DividendYield', 'N/A')}%
    Profit Margin: {overview_data.get('ProfitMargin', 'N/A')}%
    """
    
    analysis_prompt = f"""
    You are a fundamental analyst at a top investment firm. Analyze the following fundamental data and provide:
    1. A fundamental score from 0-100 (100 being strongest fundamentals)
    2. A detailed explanation of why you gave this score
    
    Fundamental Data:
    {fundamental_summary}
    
    Return your analysis as a JSON object with keys: 'score', 'explanation'
    """
    
    try:
        response = gen_model.generate_content(analysis_prompt)
        result_text = response.text
        
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_string = result_text[json_start:json_end]
            result = json.loads(json_string)
            return result
        else:
            score = calculate_basic_score(overview_data)
            return {
                'score': score,
                'explanation': 'Basic fundamental scoring applied based on key ratios.'
            }
    except Exception as e:
        score = calculate_basic_score(overview_data)
        return {
            'score': score,
            'explanation': f'AI analysis failed: {e}. Basic fundamental scoring applied.'
        }

def calculate_basic_score(overview_data):
    """Calculate a basic fundamental score without AI"""
    if not overview_data:
        return 50
    
    score = 50
    
    try:
        pe_ratio = float(overview_data.get('PERatio', 0))
        if 10 <= pe_ratio <= 25:
            score += 10
        elif pe_ratio < 10 or pe_ratio > 35:
            score -= 10
        
        roe = float(overview_data.get('ROE', 0))
        if roe > 15:
            score += 15
        elif roe < 5:
            score -= 10
        
        current_ratio = float(overview_data.get('CurrentRatio', 0))
        if current_ratio > 1.5:
            score += 5
        elif current_ratio < 1:
            score -= 5
        
        debt_equity = float(overview_data.get('DebtToEquityRatio', 0))
        if debt_equity < 0.5:
            score += 10
        elif debt_equity > 1.5:
            score -= 10
    except:
        pass
    
    return min(max(score, 0), 100)

@st.cache_data(ttl=3600)
def analyze_fundamentals(ticker, use_demo=False):
    """Main function to analyze fundamentals for a ticker"""
    if use_demo:
        overview_data = generate_demo_fundamental_data(ticker)
    else:
        overview_data = get_company_overview(ticker)
        if not overview_data:
            overview_data = generate_demo_fundamental_data(ticker)
    
    analysis_result = calculate_fundamental_score(overview_data)
    
    return {
        'score': analysis_result['score'],
        'explanation': analysis_result['explanation'],
        'essential_ratios': {
            'P/E Ratio': overview_data.get('PERatio', 'N/A'),
            'P/B Ratio': overview_data.get('PriceToBookRatio', 'N/A'),
            'ROE': f"{overview_data.get('ROE', 'N/A')}%",
            'Current Ratio': overview_data.get('CurrentRatio', 'N/A'),
            'Debt-to-Equity': overview_data.get('DebtToEquityRatio', 'N/A'),
            'Market Cap': f"${overview_data.get('MarketCapitalization', 'N/A')}"
        },
        'growth_metrics': {
            'Revenue Per Share': f"${overview_data.get('RevenuePerShareTTM', 'N/A')}",
            'EPS Growth': overview_data.get('EPS', 'N/A'),
            'Dividend Yield': f"{overview_data.get('DividendYield', 'N/A')}%",
            'Free Cash Flow': 'N/A'
        }
    }