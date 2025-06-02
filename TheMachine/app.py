# app.py - Complete Main application with 4-Pillar Analysis
import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from data_handler import download_stock_data, create_demo_data
from analysis import analyze_ticker
from sentiment import analyze_sentiment, get_company_name
from fundamental_analysis import analyze_fundamentals_weighted
from market_risk_analysis import analyze_market_risk_macro
from config import ANALYSIS_WEIGHTS, TECHNICAL_INDICATOR_WEIGHTS, FUNDAMENTAL_RATIO_WEIGHTS, GROWTH_METRICS_WEIGHTS

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

def map_market_risk_to_score(risk_score):
    """Convert market risk score to investment score (-1 to 1, inverted)"""
    # Higher risk = lower investment score
    normalized_risk = (risk_score - 50) / 50  # Convert to -1 to 1 scale
    return -normalized_risk  # Invert: high risk = negative score

def process_data(tickers, start_date, end_date, indicators, use_demo_data, investing_type, current_weights):
    """Process stock data for analysis with 4-pillar strategy context"""
    st.session_state.update({
        "start_date": start_date, "end_date": end_date, "indicators_used": indicators,
        "investing_type": investing_type, "analysis_weights": current_weights, 
        "use_demo_data": use_demo_data
    })
    
    with st.spinner(f"TheMachine is analyzing with {investing_type} strategy (4-Pillar Analysis)..."):
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
            st.sidebar.success(f"Data loaded for {len(stock_data)} stocks with {investing_type} 4-Pillar weights")
        else:
            st.sidebar.error("No data loaded. Try using Demo Data option.")
            
        progress_bar.empty()

def analyze_and_display_data():
    """Analyze and display stock data with intelligent 4-pillar weighting"""
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
                
                # Price metrics with corrected daily change color
                if not data.empty:
                    latest_close = data['Close'].iloc[-1]
                    prev_close = data['Close'].iloc[-2] if len(data) > 1 else None
                    
                    if prev_close and prev_close != 0:
                        daily_change = ((latest_close - prev_close) / prev_close) * 100
                    else:
                        daily_change = None
                    
                    st.markdown("### 📈 Key Metrics")
                    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                    metrics_col1.metric("Latest Close", f"${latest_close:.2f}")
                    
                    if daily_change is not None:
                        # Fixed color logic: remove delta_color to let Streamlit auto-handle
                        metrics_col2.metric(
                            "Daily Change", 
                            f"{daily_change:.2f}%", 
                            delta=f"{daily_change:.2f}%"
                        )
                    else:
                        metrics_col2.metric("Daily Change", "N/A")
                    
                    metrics_col3.metric("52-Week Range", f"${data['Low'].min():.2f} - ${data['High'].max():.2f}")
                
                # Split page into two columns for Sentiment and Market Risk
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
                    
                    # Market Risk & Macro Analysis
                    st.markdown("### ⚠️ Market Risk & Macro Analysis")
                    
                    if f"market_risk_results_{ticker}" not in st.session_state:
                        # Calculate market risk analysis
                        market_risk_result = analyze_market_risk_macro(ticker, investing_type, use_demo_data)
                        st.session_state[f"market_risk_results_{ticker}"] = market_risk_result
                    else:
                        market_risk_result = st.session_state[f"market_risk_results_{ticker}"]
                    
                    # Display Market Risk Score and Environment
                    risk_score = market_risk_result['risk_score']
                    environment = market_risk_result['environment']
                    env_color = market_risk_result['env_color']
                    
                    st.markdown(f"""
                    <div style="padding: 10px; background-color: {env_color}; 
                                border-radius: 5px; text-align: center; margin-bottom: 15px;">
                        <h3 style="margin: 0; color: black">
                            Market Environment: {environment} (Risk Score: {risk_score}/100)
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display data source
                    st.markdown(f"**Data Source:** {market_risk_result.get('data_source', 'Unknown')}")
                    
                    # Key Market Metrics
                    market_data = market_risk_result['market_data']
                    economic_data = market_risk_result['economic_data']
                    sector_data = market_risk_result['sector_data']
                    
                    # Market metrics in columns
                    risk_col1, risk_col2 = st.columns(2)
                    
                    with risk_col1:
                        st.markdown("**Market Indicators:**")
                        vix_color = "red" if market_data['vix_current'] > 30 else "orange" if market_data['vix_current'] > 20 else "green"
                        st.markdown(f"• **VIX (Fear Index):** <span style='color: {vix_color}; font-weight: bold;'>{market_data['vix_current']:.1f}</span>", unsafe_allow_html=True)
                        
                        rate_color = "red" if market_data['treasury_10y'] > 5 else "orange" if market_data['treasury_10y'] > 4 else "green"
                        st.markdown(f"• **10Y Treasury:** <span style='color: {rate_color}; font-weight: bold;'>{market_data['treasury_10y']:.2f}%</span>", unsafe_allow_html=True)
                        
                        spy_color = "green" if market_data['spy_performance'] > 0 else "red"
                        st.markdown(f"• **S&P 500 (5-day):** <span style='color: {spy_color}; font-weight: bold;'>{market_data['spy_performance']:+.1f}%</span>", unsafe_allow_html=True)
                    
                    with risk_col2:
                        st.markdown("**Economic Indicators:**")
                        gdp_color = "green" if economic_data['gdp_growth'] > 2.5 else "orange" if economic_data['gdp_growth'] > 1.5 else "red"
                        st.markdown(f"• **GDP Growth:** <span style='color: {gdp_color}; font-weight: bold;'>{economic_data['gdp_growth']:.1f}%</span>", unsafe_allow_html=True)
                        
                        inflation_color = "red" if economic_data['inflation_rate'] > 4 else "orange" if economic_data['inflation_rate'] > 3 else "green"
                        st.markdown(f"• **Inflation Rate:** <span style='color: {inflation_color}; font-weight: bold;'>{economic_data['inflation_rate']:.1f}%</span>", unsafe_allow_html=True)
                        
                        st.markdown(f"• **{sector_data['sector']} Sector:** <span style='font-weight: bold;'>{sector_data['sector_performance']:+.1f}% vs Market</span>", unsafe_allow_html=True)
                    
                    # Key Risk Factors
                    st.markdown("**Key Risk Factors:**")
                    risk_factors = market_risk_result['key_risk_factors']
                    for factor in risk_factors:
                        st.markdown(f"• {factor}")
                    
                    # Strategy-specific market risk context
                    strategy_context = {
                        "Swing Trading": "Monitor VIX spikes and sector rotation for optimal entry/exit timing",
                        "Value Investing": "Economic weakness may create opportunities, but watch for value traps",
                        "Growth Investing": "Rising rates and economic slowdown pose significant headwinds to growth",
                        "Balanced Approach": "Consider risk-adjusted position sizing based on current environment"
                    }
                    
                    st.markdown(f"**{investing_type} Context:** *{strategy_context.get(investing_type, 'Monitor risk factors for strategy alignment')}*")

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
                        st.markdown(f"**Data Source:** {fundamental_results.get('data_source', 'Unknown')}")
                        
                        # Strategy-specific ratio display
                        st.markdown("**Key Ratios for " + investing_type + ":**")
                        ratios = fundamental_results['essential_ratios']
                        
                        # Highlight most important ratios for this strategy
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
                        
                        st.markdown("-------------------")
                        st.markdown("**Growth Metrics:**")
                        growth_metrics = fundamental_results['growth_metrics']
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
                        
                        st.markdown("**Strategy-Weighted Analysis:**")
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #4CAF50; color: black">
                            <p style="margin: 0; line-height: 1.6; color: black">
                                {fundamental_results.get('explanation', 'No explanation available.')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Enhanced Combined Analysis with 4-way weighting
                st.markdown("---")
                st.markdown("### 🎯 4-Pillar Intelligent Analysis")
                st.markdown(f"**Strategy: {investing_type}** - Weights all four analysis pillars by relevance")
                
                # Calculate enhanced scores with 4-way strategy weighting
                tech_score = map_prediction_to_score(technical_prediction)
                fund_score = (fundamental_results['score'] - 50) / 50
                sent_score = map_sentiment_to_score(sentiment_results['sentiment']) if f"sentiment_results_{ticker}" in st.session_state else 0
                market_risk_score = map_market_risk_to_score(risk_score)
                
                # Apply 4-way strategy-based weights
                weights = current_weights
                combined_score = (tech_score * weights['technical']/100 + 
                                fund_score * weights['fundamental']/100 + 
                                sent_score * weights['sentiment']/100 +
                                market_risk_score * weights['market_risk']/100)
                
                final_prediction = map_score_to_prediction(combined_score)
                
                st.session_state["combined_results"][ticker] = {
                    "prediction": final_prediction, "score": combined_score,
                    "weights_used": weights, "investing_type": investing_type,
                    "market_risk_score": risk_score
                }
                
                prediction_color = get_prediction_color(final_prediction)
                st.markdown(f"""
                <div style="padding: 15px; background-color: {prediction_color}; 
                            border-radius: 8px; text-align: center; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: {'white' if final_prediction in ['Strong Increase', 'Strong Decrease'] else 'black'}">
                        Final 4-Pillar Prediction: {final_prediction}
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced breakdown with 4-way analysis
                col_breakdown1, col_breakdown2 = st.columns(2)
                
                with col_breakdown1:
                    st.markdown("**4-Pillar Analysis Breakdown:**")
                    st.markdown(f"""
                    - **Technical Analysis**: {technical_prediction} (Weight: {weights['technical']}%)
                    - **Fundamental Analysis**: {fundamental_results['score']}/100 (Weight: {weights['fundamental']}%)
                    - **Sentiment Analysis**: {sentiment_results['sentiment']} (Weight: {weights['sentiment']}%)
                    - **Market Risk Analysis**: {environment} - {risk_score}/100 (Weight: {weights['market_risk']}%)
                    """)
                
              #  with col_breakdown2:
               #     st.markdown("**Risk-Adjusted Strategy Context:**")
                #    if risk_score > 70:
                 #       st.markdown("🔴 **High Risk Environment**: Consider reducing position sizes or defensive strategies")
                  #  elif risk_score > 50:
                   #     st.markdown("🟡 **Moderate Risk Environment**: Standard position sizing with increased monitoring")
                    #else:
                     #   st.markdown("🟢 **Low Risk Environment**: Favorable conditions for increased allocation")
                    
                    #strategy_risk_context = {
                     #   "Swing Trading": f"VIX at {market_data['vix_current']:.1f} - {'High volatility creates opportunities' if market_data['vix_current'] > 25 else 'Low volatility may limit profits'}",
                      #  "Value Investing": f"Economic growth at {economic_data['gdp_growth']:.1f}% - {'Recession fears may create value opportunities' if economic_data['gdp_growth'] < 2 else 'Strong economy supports value recovery'}",
                       # "Growth Investing": f"Interest rates at {market_data['treasury_10y']:.1f}% - {'High rates pressure growth valuations' if market_data['treasury_10y'] > 4.5 else 'Low rates support growth premiums'}",
                        #"Balanced Approach": f"Market risk score {risk_score}/100 suggests {'defensive positioning' if risk_score > 60 else 'normal allocation' if risk_score > 40 else 'opportunistic positioning'}"
                   # }
                   # st.markdown(f"*{strategy_risk_context.get(investing_type, 'Monitor all risk factors for optimal strategy execution')}*")
                
                # 4-Pillar Strategy-Specific Insights
                st.markdown("**4-Pillar Strategy Insights:**")
                if investing_type == "Value Investing":
                    pe_ratio = fundamental_results['essential_ratios'].get('P/E Ratio', 'N/A')
                    dividend = fundamental_results['growth_metrics'].get('Dividend Yield', 'N/A')
                    st.info(f"💎 **Value + Risk Focus**: P/E {pe_ratio}, Dividend {dividend} | Market Risk: {environment} - {'Wait for better entry' if risk_score > 60 else 'Favorable value environment'}")
                
                elif investing_type == "Growth Investing":
                    revenue_growth = fundamental_results['growth_metrics'].get('Revenue Per Share', 'N/A')
                    profit_margin = fundamental_results['growth_metrics'].get('Profit Margin', 'N/A')
                    interest_impact = "Headwind" if market_data['treasury_10y'] > 4.5 else "Neutral" if market_data['treasury_10y'] > 3.5 else "Tailwind"
                    st.info(f"📈 **Growth + Macro Focus**: Revenue growth {revenue_growth}, Margin {profit_margin} | Interest Rate Impact: {interest_impact}")
                
                elif investing_type == "Swing Trading":
                    current_price = data['Close'].iloc[-1]
                    sma_20 = data['Close'].rolling(20).mean().iloc[-1] if len(data) > 20 else None
                    vix_trading = "High vol creates opportunities" if market_data['vix_current'] > 25 else "Low vol reduces profits" if market_data['vix_current'] < 15 else "Normal trading environment"
                    if sma_20:
                        position = "above" if current_price > sma_20 else "below"
                        st.info(f"🔄 **Swing + Volatility Focus**: Price ${current_price:.2f} {position} SMA ${sma_20:.2f} | VIX {market_data['vix_current']:.1f}: {vix_trading}")
                    else:
                        st.info(f"🔄 **Swing + Volatility Focus**: VIX {market_data['vix_current']:.1f}: {vix_trading}")
                
                else:  # Balanced Approach
                    overall_health = "Strong" if (fundamental_results['score'] > 70 and risk_score < 50) else "Moderate" if (fundamental_results['score'] > 50 and risk_score < 70) else "Weak"
                    st.info(f"⚖️ **Balanced + Risk-Adjusted Focus**: Overall health {overall_health} | Technical: {technical_prediction}, Market Risk: {environment}")

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
    st.header("**The Soul Beyond Data**")

# Sidebar configuration
st.sidebar.header("TheMachine Setup")

# MAIN CONFIGURATION FORM
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
        #"Balanced Approach": "⚖️ Focus: Combination of technical, fundamental, sentiment, and market risk"
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
    
    # Get analysis weights for 4-pillar system
    current_weights = ANALYSIS_WEIGHTS.get(investing_type, ANALYSIS_WEIGHTS["Balanced Approach"])
    
    # Submit button
    submitted = st.form_submit_button("Run TheMachine", use_container_width=True)

# OUTSIDE THE FORM - Display selected indicators info
#if indicators:
    #st.sidebar.success(f"✅ {len(indicators)} indicators selected")
    
    # Show selected indicators by category
 #   with st.sidebar.expander("📋 Selected Indicators Summary"):
  #      if trend_indicators:
   #         st.write(f"**Trend**: {', '.join(trend_indicators)}")
    #    if volatility_indicators:
     #       st.write(f"**Volatility**: {', '.join(volatility_indicators)}")
      #  if momentum_indicators:
       #     st.write(f"**Momentum**: {', '.join(momentum_indicators)}")
       # if volume_indicators:
        #    st.write(f"**Volume**: {', '.join(volume_indicators)}")
    
    # Show 4-pillar weights for this strategy
    #with st.sidebar.expander("🎯 4-Pillar Strategy Weights"):
     #   st.write(f"**{investing_type} Weights:**")
      #  for analysis_type, weight in current_weights.items():
       #     analysis_name = analysis_type.replace('_', ' ').title()
        #    st.write(f"• **{analysis_name}**: {weight}%")
    
    # Show strategy info
    #st.sidebar.info(f"💡 **{investing_type}**: 4-Pillar analysis weighted by strategy relevance")
#else:
 #   st.sidebar.warning("⚠️ Please select at least one indicator")

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