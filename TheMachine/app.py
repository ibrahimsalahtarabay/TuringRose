# app.py - Main application
import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from data_handler import download_stock_data, create_demo_data
from analysis import analyze_ticker
from sentiment import analyze_sentiment, get_company_name
from fundamental_analysis import analyze_fundamentals
from config import ANALYSIS_WEIGHTS

st.set_page_config(layout="wide")

def get_prediction_color(prediction):
    """Get color for prediction display"""
    colors = {
        "Strong Increase": "#2E7D32", "Increase": "#4CAF50", "Weak Increase": "#8BC34A",
        "Neutral": "#FFC107", "Weak Decrease": "#FF9800", "Decrease": "#FF5722",
        "Strong Decrease": "#D32F2F", "Error": "#9E9E9E", "N/A": "#9E9E9E"
    }
    return colors.get(prediction, "#9E9E9E")

def map_prediction_to_score(prediction):
    """Map prediction to numeric score (-1 to 1)"""
    mapping = {
        "Strong Increase": 1.0, "Increase": 0.67, "Weak Increase": 0.33,
        "Neutral": 0.0, "Weak Decrease": -0.33, "Decrease": -0.67, "Strong Decrease": -1.0
    }
    return mapping.get(prediction, 0.0)

def map_sentiment_to_score(sentiment):
    """Map sentiment to numeric score (-1 to 1)"""
    mapping = {"Positive": 1.0, "Neutral": 0.0, "Negative": -1.0}
    return mapping.get(sentiment, 0.0)

def map_score_to_prediction(score):
    """Map numeric score back to prediction"""
    if score >= 0.75: return "Strong Increase"
    elif score >= 0.33: return "Increase"
    elif score >= 0.0: return "Weak Increase"
    elif score >= -0.33: return "Weak Decrease"
    elif score >= -0.75: return "Decrease"
    else: return "Strong Decrease"

def process_data(tickers, start_date, end_date, indicators, use_demo_data, investing_type, current_weights):
    """Process stock data for analysis"""
    st.session_state.update({
        "start_date": start_date, "end_date": end_date, "indicators_used": indicators,
        "investing_type": investing_type, "analysis_weights": current_weights, "use_demo_data": use_demo_data
    })
    
    with st.spinner("TheMachine is analyzing..."):
        stock_data = {}
        progress_bar = st.progress(0)
        
        for i, ticker in enumerate(tickers):
            progress = (i / len(tickers))
            progress_bar.progress(progress)
            
            if use_demo_data:
                data = create_demo_data(ticker)
                time.sleep(0.5)
                stock_data[ticker] = data
            else:
                data = download_stock_data(ticker, start_date, end_date)
                if not data.empty:
                    stock_data[ticker] = data
                else:
                    st.sidebar.warning(f"No data found for {ticker}.", icon="⚠️")
            
            if i < len(tickers) - 1 and not use_demo_data:
                time.sleep(1)
        
        progress_bar.progress(1.0)
        st.session_state["stock_data"] = stock_data
        st.session_state["analysis_complete"] = True
        
        if stock_data:
            st.sidebar.success(f"Data loaded for {len(stock_data)} stocks")
        else:
            st.sidebar.error("No data loaded. Try using Demo Data option.")
            
        progress_bar.empty()

def analyze_and_display_data():
    """Analyze and display stock data"""
    indicators = st.session_state.get("indicators_used", [])
    investing_type = st.session_state.get("investing_type", "Balanced Approach")
    current_weights = st.session_state.get("analysis_weights", {})
    start_date = st.session_state.get("start_date", datetime.today() - timedelta(days=365))
    end_date = st.session_state.get("end_date", datetime.today())
    use_demo_data = st.session_state.get("use_demo_data", True)
    
    tab_names = list(st.session_state["stock_data"].keys())
    tabs = st.tabs(tab_names)
    overall_results = []
    
    if "analysis_results" not in st.session_state:
        st.session_state["analysis_results"] = {}
    if "combined_results" not in st.session_state:
        st.session_state["combined_results"] = {}

    for i, ticker in enumerate(st.session_state["stock_data"]):
        data = st.session_state["stock_data"][ticker]
        
        with tabs[i]:
            with st.spinner(f"Analyzing {ticker}..."):
                fig, technical_result = analyze_ticker(ticker, data, indicators)
                
                col1, col2, col3 = st.columns(3)
                
                with col2:
                    fundamental_result = analyze_fundamentals(ticker, use_demo_data)
                    st.session_state[f"fundamental_results_{ticker}"] = fundamental_result
                
                with col3:
                    company_name = get_company_name(ticker)
                    sentiment_result = analyze_sentiment(ticker, start_date, end_date, api_key=None, use_demo=use_demo_data)
                    st.session_state[f"sentiment_results_{ticker}"] = sentiment_result
                
                st.session_state["analysis_results"][ticker] = technical_result
                
                technical_prediction = technical_result.get("action", "N/A")
                prediction_map = {
                    "Strong Buy": "Strong Increase", "Buy": "Increase", "Weak Buy": "Weak Increase", 
                    "Hold": "Neutral", "Weak Sell": "Weak Decrease", "Sell": "Decrease", 
                    "Strong Sell": "Strong Decrease", "Error": "Error", "N/A": "N/A"
                }
                
                mapped_prediction = prediction_map.get(technical_prediction, technical_prediction)
                overall_results.append({"Stock": ticker, "Prediction": mapped_prediction})
                
                # Display results
                st.subheader(f"Analysis for {ticker}")
                st.plotly_chart(fig, use_container_width=True)
                
                # Technical Analysis
                st.markdown("### 📊 Technical Analysis")
                action_color = {
                    "Strong Buy": "lightgreen", "Buy": "lightgreen", "Weak Buy": "lightgreen",
                    "Hold": "gold", "Weak Sell": "salmon", "Sell": "salmon", 
                    "Strong Sell": "salmon", "Error": "gray", "N/A": "gray"
                }.get(technical_prediction, "gray")
                
                st.markdown(f"""
                <div style="padding: 10px; background-color: {action_color}; 
                            border-radius: 5px; text-align: center; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: black">
                        Technical Signal: {technical_prediction}
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #1f77b4; color: black">
                    <p style="margin: 0; line-height: 1.6; color: black">
                        {technical_result.get("justification", "No technical analysis provided.")}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Price metrics
                if not data.empty:
                    latest_close = data['Close'].iloc[-1]
                    prev_close = data['Close'].iloc[-2] if len(data) > 1 else None
                    daily_change = ((latest_close - prev_close) / prev_close * 100) if prev_close else None
                    
                    st.markdown("### 📈 Key Metrics")
                    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                    metrics_col1.metric("Latest Close", f"${latest_close:.2f}")
                    
                    if daily_change is not None:
                        delta_color = "normal" if daily_change >= 0 else "inverse"
                        metrics_col2.metric("Daily Change", f"{daily_change:.2f}%", delta=f"{daily_change:.2f}%", delta_color=delta_color)
                    
                    metrics_col3.metric("52-Week Range", f"${data['Low'].min():.2f} - ${data['High'].max():.2f}")
                
                # Split page into two columns
                st.markdown("---")
                col_left, col_right = st.columns(2)
                
                # Sentiment Analysis
                with col_left:
                    st.markdown("### 📰 Sentiment Analysis")
                    
                    if f"sentiment_results_{ticker}" in st.session_state:
                        sentiment_results = st.session_state[f"sentiment_results_{ticker}"]
                        
                        if "error" in sentiment_results:
                            st.error(sentiment_results["error"])
                        else:
                            sentiment_label = sentiment_results["sentiment"]
                            sentiment_color = {
                                "Positive": "lightgreen", "Negative": "salmon", "Neutral": "gold"
                            }.get(sentiment_label, "gray")
                            
                            st.markdown(f"""
                            <div style="padding: 10px; background-color: {sentiment_color}; 
                                        border-radius: 5px; text-align: center; margin-bottom: 15px;">
                                <h3 style="margin: 0; color: black">
                                    Overall Sentiment: {sentiment_label} ({sentiment_results["score"]:.2f})
                                </h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"**Articles Analyzed:** {sentiment_results['articles_analyzed']}")
                            st.markdown(f"**Keyword Used:** {sentiment_results.get('keyword_used', 'N/A')}")
                            
                            if sentiment_results["sample_articles"]:
                                st.markdown("**Sample Articles:**")
                                for article in sentiment_results["sample_articles"][:3]:
                                    article_sentiment = article["sentiment"]
                                    article_color = {
                                        "positive": "lightgreen", "negative": "salmon", "neutral": "gold"
                                    }.get(article_sentiment, "gray")
                                    
                                    st.markdown(f"""
                                    <div style="padding: 8px; border-left: 5px solid {article_color}; margin-bottom: 10px;">
                                        <p style="margin: 0; font-weight: bold; font-size: 0.9rem;">{article["headline"]}</p>
                                        <p style="margin: 0; font-size: 0.8em;">Sentiment: {article_sentiment.capitalize()} ({article["score"]:.2f})</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            st.markdown("**Sentiment Analysis Description:**")
                            st.markdown(f"""
                            Based on analysis of {sentiment_results['articles_analyzed']} articles, the overall sentiment is **{sentiment_label}** 
                            with a score of {sentiment_results["score"]:.2f}. This suggests that market perception toward {ticker} is currently 
                            {sentiment_label.lower()}, which may influence short-term price movements.
                            """)
                
                # Fundamental Analysis
                with col_right:
                    st.markdown("### 📊 Fundamental Analysis")
                    
                    if f"fundamental_results_{ticker}" in st.session_state:
                        fundamental_results = st.session_state[f"fundamental_results_{ticker}"]
                        
                        score = fundamental_results['score']
                        score_color = "lightgreen" if score >= 70 else "gold" if score >= 50 else "salmon"
                        
                        st.markdown(f"""
                        <div style="padding: 10px; background-color: {score_color}; 
                                    border-radius: 5px; text-align: center; margin-bottom: 15px;">
                            <h3 style="margin: 0; color: black">
                                Overall Fundamental Score: {score}/100
                            </h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("**Essential Ratios:**")
                        ratios = fundamental_results['essential_ratios']
                        for key, value in ratios.items():
                            st.markdown(f"• **{key}:** {value}")
                        
                        st.markdown("**Growth Metrics:**")
                        metrics = fundamental_results['growth_metrics']
                        for key, value in metrics.items():
                            st.markdown(f"• **{key}:** {value}")
                        
                        st.markdown("**Fundamental Analysis Description:**")
                        st.markdown(fundamental_results.get('explanation', 'No explanation available.'))
                
                # Combined Analysis
                st.markdown("---")
                st.markdown("### 🎯 Combined Analysis (Technical + Fundamental + Sentiment)")
                
                tech_score = map_prediction_to_score(technical_prediction)
                fund_score = (fundamental_results['score'] - 50) / 50
                sent_score = map_sentiment_to_score(sentiment_results['sentiment']) if f"sentiment_results_{ticker}" in st.session_state else 0
                
                weights = current_weights
                combined_score = (tech_score * weights['technical']/100 + 
                                fund_score * weights['fundamental']/100 + 
                                sent_score * weights['sentiment']/100)
                
                final_prediction = map_score_to_prediction(combined_score)
                
                st.session_state["combined_results"][ticker] = {
                    "prediction": final_prediction, "score": combined_score,
                    "weights_used": weights, "investing_type": investing_type
                }
                
                prediction_color = get_prediction_color(final_prediction)
                st.markdown(f"""
                <div style="padding: 15px; background-color: {prediction_color}; 
                            border-radius: 8px; text-align: center; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: {'white' if final_prediction in ['Strong Increase', 'Strong Decrease'] else 'black'}">
                        Combined Prediction: {final_prediction}
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                **Analysis Breakdown** *(Strategy: {investing_type})*:
                - **Technical Analysis**: {technical_prediction} (Weight: {weights['technical']}%)
                - **Fundamental Analysis**: Score {fundamental_results['score']}/100 (Weight: {weights['fundamental']}%)
                - **Sentiment Analysis**: {sentiment_results['sentiment']} (Weight: {weights['sentiment']}%)
                
                The combined prediction is based on your selected strategy ({investing_type}) which emphasizes different 
                aspects of the analysis according to the specified weights.
                """)

    st.session_state["overall_results"] = overall_results

def display_static_pages():
    """Display placeholder when no analysis is run"""
    st.info("Please configure your analysis parameters in the sidebar and click 'Run TheMachine' to begin.")

# =============================================================================
# Main Application
if "page_initialized" not in st.session_state:
    st.session_state.page_initialized = True

# Display title
col1, col2 = st.columns([4, 2])
with col1:
    st.image("TheMachine/assets/logo1.png", width=250)
    st.header("**Superior Machine: Go Farther, Faster, With Unmatched Precision.**")

# Sidebar configuration
with st.sidebar.form("config_form"):
    st.header("TheMachine Setup")
    
    # Stock tickers input
    tickers_input = st.text_input("Enter Stock Tickers (comma-separated):", "AAPL,MSFT,GOOG")
    tickers = [ticker.strip().upper() for ticker in tickers_input.split(",") if ticker.strip()]
    
    # Investing type
    st.markdown("---")
    investing_type = st.selectbox(
        "Investing Type:",
        ["Value investing", "Balanced Approach", "Day/Swing Trading"],
        index=1
    )
    
    # Date range
    st.markdown("---")
    start_date = st.date_input("Start Date:", value=datetime.today() - timedelta(days=365))
    end_date = datetime.today()
    
    # Technical indicators
    st.markdown("---")
    st.subheader("Technical Indicators")
    indicators = st.multiselect(
        "Select Indicators:",
        ["20-Day SMA", "20-Day EMA", "20-Day Bollinger Bands", "VWAP"],
        default=["20-Day SMA"]
    )
    
    # Demo data option
    st.markdown("---")
    use_demo_data = st.checkbox("Use Demo Data", value=True)
    
    # Get analysis weights
    current_weights = ANALYSIS_WEIGHTS[investing_type]
    
    # Submit button
    submitted = st.form_submit_button("🚀 Run TheMachine")

# Process form submission
if submitted:
    st.session_state["use_demo_data"] = use_demo_data
    process_data(tickers, start_date, end_date, indicators, use_demo_data, investing_type, current_weights)
    st.rerun()

# Display results or placeholder
if "stock_data" in st.session_state and st.session_state["stock_data"]:
    analyze_and_display_data()
else:
    display_static_pages()