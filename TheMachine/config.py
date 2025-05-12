# config.py - Configuration settings for the application

import streamlit as st
from datetime import datetime, timedelta
import google.generativeai as genai

# API Keys - In a production environment, these should be stored in environment variables or Streamlit secrets
GOOGLE_API_KEY = "AIzaSyD2mJ94OSl1zZeAgOmvveYu5CAToo9X_Ag"
ALPHA_VANTAGE_API_KEY = "NLKISJ9TBY2KCC6D"

# News API Configuration - Updated with your actual API key (now unused)
NEWS_API_KEY = None  # Disabled as per request

# Model configuration
MODEL_NAME = 'gemini-2.0-flash'

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)
gen_model = genai.GenerativeModel(MODEL_NAME)

# Analysis weights for different strategies
ANALYSIS_WEIGHTS = {
    'Value investing': {
        'technical': 20,
        'fundamental': 60,
        'sentiment': 20
    },
    'Balanced Approach': {
        'technical': 35,
        'fundamental': 45,
        'sentiment': 20
    },
    'Day/Swing Trading': {
        'technical': 60,
        'fundamental': 20,
        'sentiment': 20
    }
}

def setup_page():
    """Configure the Streamlit page settings"""
    st.set_page_config(layout="wide")

def setup_sidebar():
    """Configure the sidebar controls and return user inputs"""
    # This is kept for compatibility, but no longer used actively in the form-based approach
    st.sidebar.header("TheMachine Setup")
    
    # Input for multiple stock tickers (comma-separated)
    tickers_input = st.sidebar.text_input("Enter Stock Tickers (comma-separated):", "AAPL,MSFT,GOOG")
    # Parse tickers by stripping extra whitespace and splitting on commas
    tickers = [ticker.strip().upper() for ticker in tickers_input.split(",") if ticker.strip()]
    
    # Investing Type dropdown
    st.sidebar.markdown("---")
    investing_type = st.sidebar.selectbox(
        "Investing Type:",
        ["Value investing", "Balanced Approach", "Day/Swing Trading"],
        index=1  # Default to Balanced Approach
    )
    
    # Time Range input (default dimmed)
    st.sidebar.markdown("---")
    
    if investing_type == "Value investing":
        # Enable time range for 1-10 years
        time_range_years = st.sidebar.slider("Time Range (Years):", 1, 10, 1)
        days_back = time_range_years * 365
        start_date = datetime.today() - timedelta(days=days_back)
        start_date_widget = st.sidebar.date_input("Start Date:", value=start_date, disabled=True, help="Automatically calculated based on time range")
    elif investing_type == "Day/Swing Trading":
        # Enable time range for 1-365 days
        time_range_days = st.sidebar.slider("Time Range (Days):", 1, 365, 30)
        start_date = datetime.today() - timedelta(days=time_range_days)
        start_date_widget = st.sidebar.date_input("Start Date:", value=start_date, disabled=True, help="Automatically calculated based on time range")
    else:  # Balanced Approach
        # Time range dimmed, start date enabled
        st.sidebar.markdown("*Time Range (Fixed for Balanced Approach)*")
        start_date = st.sidebar.date_input("Start Date:", value=datetime.today() - timedelta(days=365))
        
    # End date is always today (not shown to user)
    end_date = datetime.today()
    
    # Technical indicators selection (applied to every ticker)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Technical Indicators")
    indicators = st.sidebar.multiselect(
        "Select Indicators:",
        ["20-Day SMA", "20-Day EMA", "20-Day Bollinger Bands", "VWAP"],
        default=["20-Day SMA"]
    )
    
    # Add option to use demo data
    st.sidebar.markdown("---")
    use_demo_data = st.sidebar.checkbox("Use Demo Data", value=True)  # Default to true since we're disabling News API
    
    # Always use demo/RSS data for sentiment analysis
    use_sentiment_analysis = True
    news_api_key = None  # Disabled as per request
    sentiment_keywords = ""
    
    # Get analysis weights based on investing type
    current_weights = ANALYSIS_WEIGHTS[investing_type]
    
    return (tickers, start_date, end_date, indicators, use_sentiment_analysis, 
            news_api_key, sentiment_keywords, use_demo_data, investing_type, 
            current_weights)