# app.py - Main application
import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from data_handler import download_stock_data, create_demo_data
from analysis import analyze_ticker
from sentiment import analyze_sentiment, get_company_name
from fundamental_analysis import analyze_fundamentals_weighted
from config import ANALYSIS_WEIGHTS, calculate_weighted_technical_score

st.set_page_config(layout="wide")

def map_prediction_to_score(prediction):
    """Map prediction to numeric score (-1 to 1)"""
    mapping = {
        "Strong Increase": 1.0, "Increase": 0.67, "Weak Increase": 0.33,
        "Neutral": 0.0, "Weak Decrease": -0.33, "Decrease": -0.67, "Strong Decrease": -1.0,
        "Strong Buy": 1.0, "Buy": 0.67, "Weak Buy": 0.33,
        "Hold": 0.0, "Weak Sell": -0.33, "Sell": -0.67, "Strong Sell": -1.0
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

def get_prediction_color(prediction):
    """Get color for prediction display"""
    colors = {
        "Strong Increase": "#2E7D32", "Increase": "#4CAF50", "Weak Increase": "#8BC34A",
        "Neutral": "#FFC107", "Weak Decrease": "#FF9800", "Decrease": "#FF5722",
        "Strong Decrease": "#D32F2F", "Error": "#9E9E9E", "N/A": "#9E9E9E"
    }
    return colors.get(prediction, "#9E9E9E")

# Update process_data function to store investing type
def process_data(tickers, start_date, end_date, indicators, use_demo_data, investing_type, current_weights):
    """Process stock data for analysis with strategy context"""
    st.session_state.update({
        "start_date": start_date, "end_date": end_date, "indicators_used": indicators,
        "investing_type": investing_type, "analysis_weights": current_weights, 
        "use_demo_data": use_demo_data
    })
    
    with st.spinner(f"TheMachine is analyzing with {investing_type} strategy..."):
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
            st.sidebar.success(f"Data loaded for {len(stock_data)} stocks with {investing_type} weights")
        else:
            st.sidebar.error("No data loaded. Try using Demo Data option.")
            
        progress_bar.empty()

def analyze_and_display_data():
    """Analyze and display stock data with intelligent weighting"""
    indicators = st.session_state.get("indicators_used", [])
    investing_type = st.session_state.get("investing_type", "Balanced Approach")
    current_weights = st.session_state.get("analysis_weights", {})
    start_date = st.session_state.get("start_date", datetime.today() - timedelta(days=365))
    end_date = st.session_state.get("end_date", datetime.today())
    use_demo_data = st.session_state.get("use_demo_data", True)
    
    # Get indicator parameters from session state
    indicator_params = st.session_state.get("indicator_params", {
        'rsi_period': 14, 'macd_fast': 12, 'macd_slow': 26, 
        'bb_period': 20, 'bb_std': 2.0
    })
    
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
            with st.spinner(f"Analyzing {ticker} with {investing_type} strategy..."):
                # Technical Analysis with indicator parameters
                fig, technical_result = analyze_ticker(ticker, data, indicators, indicator_params)
                
                col1, col2, col3 = st.columns(3)
                
                with col2:
                    # Enhanced Fundamental Analysis with strategy weighting
                    fundamental_result = analyze_fundamentals_weighted(ticker, investing_type, use_demo_data)
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
                
                # Display results with strategy context
                st.subheader(f"Analysis for {ticker} ({investing_type} Strategy)")
                st.plotly_chart(fig, use_container_width=True)
                
                # Technical Analysis with strategy weighting info
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
                
                # Show indicator weighting for this strategy
                if indicators:
                    from config import TECHNICAL_INDICATOR_WEIGHTS
                    strategy_weights = TECHNICAL_INDICATOR_WEIGHTS.get(investing_type, {})
                    
                    with st.expander("📈 Strategy-Weighted Indicators"):
                        st.markdown(f"**{investing_type} Indicator Weights:**")
                        for indicator in indicators:
                            weight = strategy_weights.get(indicator, 0.5)
                            weight_text = "High" if weight >= 0.8 else "Medium" if weight >= 0.6 else "Low"
                            color = "#2E7D32" if weight >= 0.8 else "#FF9800" if weight >= 0.6 else "#9E9E9E"
                            st.markdown(f"""
                            <div style="display: flex; justify-content: space-between; padding: 5px; border-left: 3px solid {color}; margin: 5px 0;">
                                <span>{indicator}</span>
                                <span style="color: {color}; font-weight: bold;">{weight_text} ({weight:.1f})</span>
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
                        metrics_col2.metric(
                            "Daily Change", 
                            f"{daily_change:.2f}%", 
                            delta=f"{daily_change:.2f}%"
                        )
                    else:
                        metrics_col2.metric("Daily Change", "N/A")
                    
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
                
                # Enhanced Fundamental Analysis with strategy weighting
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
                                {investing_type} Score: {score}/100
                            </h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show strategy focus
                        #st.markdown(f"**Data Source:** {fundamental_results.get('data_source', 'Unknown')}")
                        
                        # Strategy-specific ratio display
                        st.markdown("**Key Ratios for " + investing_type + ":**")
                        ratios = fundamental_results['essential_ratios']
                        
                        # Highlight most important ratios for this strategy
                        from config import FUNDAMENTAL_RATIO_WEIGHTS
                        ratio_weights = FUNDAMENTAL_RATIO_WEIGHTS.get(investing_type, {})
                        
                        for key, value in ratios.items():
                            # Map display names to config keys
                            config_key = key.replace(' ', '_').replace('-', '_')
                            weight = ratio_weights.get(config_key, 0.5)
                            
                            # Color code by importance for this strategy
                            if weight >= 0.8:
                                importance = "🔴 Critical"
                                border_color = "#D32F2F"
                            elif weight >= 0.6:
                                importance = "🟡 Important"  
                                border_color = "#FF9800"
                            else:
                                importance = "⚪ Standard"
                                border_color = "#9E9E9E"
                            
                            st.markdown(f"""
                            <div style="padding: 5px; border-left: 3px solid {border_color}; margin: 5px 0;">
                                <strong>{key}:</strong> {value} <span style="font-size: 0.8em; color: {border_color};">({importance})</span>
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown("---------------")
                        st.markdown("**Growth Metrics:**")
                        growth_metrics = fundamental_results['growth_metrics']
                        from config import GROWTH_METRICS_WEIGHTS
                        growth_weights = GROWTH_METRICS_WEIGHTS.get(investing_type, {})
                        
                        for key, value in growth_metrics.items():
                            # Map display names to config keys
                            config_key = key.replace(' ', '_').replace('-', '_')
                            weight = growth_weights.get(config_key, 0.5)
                            
                            # Color code by importance for this strategy
                            if weight >= 0.8:
                                importance = "🔴 Critical"
                                border_color = "#D32F2F"
                            elif weight >= 0.6:
                                importance = "🟡 Important"
                                border_color = "#FF9800"
                            else:
                                importance = "⚪ Standard"
                                border_color = "#9E9E9E"
                            
                            st.markdown(f"""
                            <div style="padding: 5px; border-left: 3px solid {border_color}; margin: 5px 0;">
                                <strong>{key}:</strong> {value} <span style="font-size: 0.8em; color: {border_color};">({importance})</span>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown("---------------")
                        st.markdown("**Strategy-Weighted Analysis:**")
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #4CAF50; color: black">
                            <p style="margin: 0; line-height: 1.6; color: black">
                                {fundamental_results.get('explanation', 'No explanation available.')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Enhanced Combined Analysis with Strategy Weighting
                st.markdown("---")
                st.markdown("### 🎯 Intelligent Combined Analysis")
                st.markdown(f"**Strategy: {investing_type}** - Weights indicators and ratios by relevance")
                
                # Calculate enhanced scores with strategy weighting
                tech_score = map_prediction_to_score(technical_prediction)
                fund_score = (fundamental_results['score'] - 50) / 50
                sent_score = map_sentiment_to_score(sentiment_results['sentiment']) if f"sentiment_results_{ticker}" in st.session_state else 0
                
                # Apply strategy-based weights
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
                        Final Prediction: {final_prediction}
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced breakdown with strategy context
                col_breakdown1, col_breakdown2 = st.columns(2)
                
                with col_breakdown1:
                    st.markdown("**Analysis Breakdown:**")
                    st.markdown(f"""
                    - **Technical Analysis**: {technical_prediction} (Weight: {weights['technical']}%)
                    - **Fundamental Analysis**: Score {fundamental_results['score']}/100 (Weight: {weights['fundamental']}%)
                    - **Sentiment Analysis**: {sentiment_results['sentiment']} (Weight: {weights['sentiment']}%)
                    """)
                
                with col_breakdown2:
                    st.markdown("**Strategy Context:**")
                    strategy_context = {
                        "Value Investing": "Emphasizes undervaluation, financial health, and dividend income",
                        "Growth Investing": "Prioritizes revenue growth, earnings expansion, and future potential", 
                        "Swing Trading": "Focuses on technical momentum, short-term catalysts, and risk management",
                        "Balanced Approach": "Combines technical timing with fundamental strength and market sentiment"
                    }
                    st.markdown(f"*{strategy_context.get(investing_type, 'Balanced investment approach')}*")
                
                # Strategy-specific insights
                st.markdown("**Strategy-Specific Insights:**")
                if investing_type == "Value Investing":
                    pe_ratio = fundamental_results['essential_ratios'].get('P/E Ratio', 'N/A')
                    dividend = fundamental_results['growth_metrics'].get('Dividend Yield', 'N/A')
                    st.info(f"💎 **Value Focus**: P/E of {pe_ratio} and dividend yield of {dividend} are key metrics for value assessment")
                
                elif investing_type == "Growth Investing":
                    revenue_growth = fundamental_results['growth_metrics'].get('Revenue Per Share', 'N/A')
                    profit_margin = fundamental_results['growth_metrics'].get('Profit Margin', 'N/A')
                    st.info(f"📈 **Growth Focus**: Revenue growth and {profit_margin} profit margin indicate expansion potential")
                
                elif investing_type == "Swing Trading":
                    current_price = data['Close'].iloc[-1]
                    sma_20 = data['Close'].rolling(20).mean().iloc[-1] if len(data) > 20 else None
                    if sma_20:
                        position = "above" if current_price > sma_20 else "below"
                        st.info(f"🔄 **Swing Focus**: Price ${current_price:.2f} is {position} 20-day SMA ${sma_20:.2f} - key for momentum trades")
                    else:
                        st.info("🔄 **Swing Focus**: Monitor technical indicators and volume for entry/exit timing")
                
                else:  # Balanced Approach
                    st.info("⚖️ **Balanced Focus**: Combines strong fundamentals with technical timing and market sentiment for well-rounded decisions")

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
st.sidebar.header("TheMachine Setup")

# MAIN CONFIGURATION FORM - No preset buttons
with st.sidebar.form("config_form"):
    # Stock tickers input
    tickers_input = st.text_input("Enter Stock Tickers (comma-separated):", "AAPL,MSFT,GOOG")
    tickers = [ticker.strip().upper() for ticker in tickers_input.split(",") if ticker.strip()]
    
    # Investing type with dropdown preset
    investing_type = st.selectbox(
        "Investment Strategy:",
        ["Balanced Approach", "Swing Trading", "Value Investing", "Growth Investing"],
        index=0,
        help="Strategy automatically weights indicators and ratios based on investment approach"
    )
    
    # Show strategy description
    #strategy_descriptions = {
     #   "Swing Trading": "🔄 Focus: Short-term momentum, technical signals, volume patterns",
      #  "Value Investing": "💎 Focus: Undervalued stocks, financial health, dividend yield", 
       # "Growth Investing": "📈 Focus: Revenue growth, earnings expansion, future potential",
        #"Balanced Approach": "⚖️ Focus: Combination of technical, fundamental, and growth factors"
    #}
    #st.info(strategy_descriptions[investing_type])
    
    # Date range
    st.markdown("**Date Range:**")
    start_date = st.date_input("Start Date:", value=datetime.today() - timedelta(days=365))
    end_date = datetime.today()
    
    # Strategy-based indicator recommendations
    strategy_indicators = {
        "Swing Trading": {
            "trend": ["20-Day SMA", "20-Day EMA"],
            "volatility": ["20-Day Bollinger Bands"],
            "momentum": ["RSI", "MACD", "Stochastic"],
            "volume": ["VWAP"]
        },
        "Value Investing": {
            "trend": ["50-Day SMA", "200-Day SMA"],
            "volatility": ["20-Day Bollinger Bands"],
            "momentum": ["RSI"],
            "volume": []
        },
        "Growth Investing": {
            "trend": ["20-Day SMA", "50-Day SMA"],
            "volatility": ["20-Day Bollinger Bands"],
            "momentum": ["RSI", "MACD"],
            "volume": ["VWAP"]
        },
        "Balanced Approach": {
            "trend": ["20-Day SMA"],
            "volatility": ["20-Day Bollinger Bands"],
            "momentum": ["RSI", "MACD"],
            "volume": ["VWAP"]
        }
    }
    
    # Get default indicators for selected strategy
    defaults = strategy_indicators[investing_type]
    
    # Technical indicators with strategy-based defaults
    st.markdown("**Technical Indicators:**")
    
    trend_indicators = st.multiselect(
        "Trend Indicators:",
        ["20-Day SMA", "20-Day EMA", "50-Day SMA", "200-Day SMA"],
        default=defaults["trend"],
        key="trend_indicators_form"
    )
    
    volatility_indicators = st.multiselect(
        "Volatility Indicators:",
        ["20-Day Bollinger Bands", "ATR (Average True Range)"],
        default=defaults["volatility"],
        key="volatility_indicators_form"
    )
    
    momentum_indicators = st.multiselect(
        "Momentum Indicators:",
        ["RSI", "MACD", "Stochastic"],
        default=defaults["momentum"],
        key="momentum_indicators_form"
    )
    
    volume_indicators = st.multiselect(
        "Volume Indicators:",
        ["VWAP", "Volume SMA"],
        default=defaults["volume"],
        key="volume_indicators_form"
    )
    
    # Combine all selected indicators
    indicators = trend_indicators + volatility_indicators + momentum_indicators + volume_indicators
    
    # Demo data option
    st.markdown("**Data Source:**")
    use_demo_data = st.checkbox("Use Demo Data", value=True)
    
    # Advanced settings
    with st.expander("⚙️ Advanced Indicator Settings"):
        st.markdown("**Customize Indicator Parameters:**")
        rsi_period = st.slider("RSI Period", 10, 20, 14)
        macd_fast = st.slider("MACD Fast Period", 8, 16, 12)
        macd_slow = st.slider("MACD Slow Period", 20, 30, 26)
        bb_period = st.slider("Bollinger Bands Period", 15, 25, 20)
        bb_std = st.slider("Bollinger Bands Std Dev", 1.5, 2.5, 2.0)
        
        # Store parameters
        indicator_params = {
            'rsi_period': rsi_period,
            'macd_fast': macd_fast,
            'macd_slow': macd_slow,
            'bb_period': bb_period,
            'bb_std': bb_std
        }
    
    # Get analysis weights (we'll update this next)
    current_weights = ANALYSIS_WEIGHTS[investing_type] if investing_type in ANALYSIS_WEIGHTS else ANALYSIS_WEIGHTS["Balanced Approach"]
    
    # Submit button
    submitted = st.form_submit_button("Run TheMachine", use_container_width=True)

# OUTSIDE THE FORM - Display selected indicators info
if indicators:
    st.sidebar.success(f"✅ {len(indicators)} indicators selected")
    
    # Show selected indicators by category
    #with st.sidebar.expander("📋 Selected Indicators Summary"):
     #   if trend_indicators:
      #      st.write(f"**Trend**: {', '.join(trend_indicators)}")
       # if volatility_indicators:
        #    st.write(f"**Volatility**: {', '.join(volatility_indicators)}")
        #if momentum_indicators:
         #   st.write(f"**Momentum**: {', '.join(momentum_indicators)}")
        #if volume_indicators:
           # st.write(f"**Volume**: {', '.join(volume_indicators)}")
    
    # Show strategy info
    #st.sidebar.info(f"💡 **{investing_type}**: Indicators and ratios weighted by strategy relevance")
else:
    st.sidebar.warning("⚠️ Please select at least one indicator")

# Store indicator params in session state when form is submitted
if submitted:
    st.session_state["indicator_params"] = indicator_params
    st.session_state["use_demo_data"] = use_demo_data
    st.session_state["investing_type"] = investing_type  # Store strategy type
    process_data(tickers, start_date, end_date, indicators, use_demo_data, investing_type, current_weights)
    st.rerun()

# Display results or placeholder
if "stock_data" in st.session_state and st.session_state["stock_data"]:
    analyze_and_display_data()
else:
    display_static_pages()
