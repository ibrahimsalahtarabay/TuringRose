# ui_components.py - UI components for the Streamlit app

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime

def display_overall_summary(overall_results, use_sentiment_analysis):
    """Display the overall summary tab with predictions visualization"""
    st.subheader("Overall Predictions")
    
    # Create DataFrame for summary
    df_summary = pd.DataFrame(overall_results)
    
    # Count predictions by type
    if not df_summary.empty:
        pred_counts = df_summary['Prediction'].value_counts().reset_index()
        pred_counts.columns = ['Prediction', 'Count']
        
        # Display summary in columns
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.markdown("### Prediction Distribution")
            # Create a simple horizontal bar chart using Plotly
            if not pred_counts.empty:
                # Define colors for predictions
                colors = []
                for pred in pred_counts['Prediction']:
                    if 'Increase' in pred:
                        if 'Strong' in pred:
                            colors.append('#2E7D32')  # Dark green
                        elif 'Weak' in pred:
                            colors.append('#8BC34A')  # Light green
                        else:
                            colors.append('#4CAF50')  # Green
                    elif 'Decrease' in pred:
                        if 'Strong' in pred:
                            colors.append('#D32F2F')  # Dark red
                        elif 'Weak' in pred:
                            colors.append('#FF9800')  # Orange
                        else:
                            colors.append('#FF5722')  # Deep orange
                    elif pred == 'Neutral':
                        colors.append('#FFC107')  # Amber
                    else:
                        colors.append('#9E9E9E')  # Gray
                
                fig = go.Figure(go.Bar(
                    x=pred_counts['Count'],
                    y=pred_counts['Prediction'],
                    orientation='h',
                    marker=dict(color=colors)
                ))
                fig.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Stock Predictions")
            # Apply color styling to the table
            def color_prediction(val):
                color_map = {
                    'Strong Increase': 'background-color: #2E7D32; color: white',
                    'Increase': 'background-color: #4CAF50; color: white',
                    'Weak Increase': 'background-color: #8BC34A; color: black',
                    'Neutral': 'background-color: #FFC107; color: black',
                    'Weak Decrease': 'background-color: #FF9800; color: black',
                    'Decrease': 'background-color: #FF5722; color: white',
                    'Strong Decrease': 'background-color: #D32F2F; color: white',
                    'Error': 'background-color: #9E9E9E; color: white',
                    'N/A': 'background-color: #9E9E9E; color: white'
                }
                return color_map.get(val, '')
            
            # Apply styling to the Prediction column
            styled_df = df_summary.style.map(color_prediction, subset=['Prediction'])
            st.dataframe(styled_df, use_container_width=True, height=350)
    
    # Disclaimer
    st.markdown("""
    ---
    **Disclaimer**: These predictions are based on technical indicators, fundamental analysis, and sentiment analysis. 
    They should not be considered as financial advice. Always do your own research and consult 
    with a professional financial advisor before making investment decisions.
    """)

#def display_footer():
    #"""Display simplified footer in sidebar"""
    #st.sidebar.markdown("---")
    # Just the version info, no About section since it's moved to main page

def display_about_section():
    """Display the About section on the main page"""
    st.markdown("---")
    st.subheader("About TuringRose")
    st.markdown("""
    TuringRose Superior Machine combines cutting-edge technical analysis, comprehensive fundamental analysis, 
    and AI-powered sentiment analysis to provide superior stock predictions. Our system adapts to different 
    investing strategies with customizable analysis weights.
    
    **Key Features:**
    - **Technical Analysis**: Advanced candlestick charts with multiple indicators (SMA, EMA, Bollinger Bands, VWAP)
    - **Fundamental Analysis**: Comprehensive evaluation using Alpha Vantage data and Gemini AI scoring
    - **Sentiment Analysis**: Real-time news sentiment using FinBERT model
    - **Strategy-Based Weighting**: Different analysis weights for Value Investing, Balanced Approach, and Day/Swing Trading
    - **Combined Predictions**: Unified predictions merging all three analysis types
    - **Export Options**: Download detailed results in CSV, Excel, or JSON formats
    """)

def display_resources_section():
    """Display the Resources section on the main page"""
    st.markdown("---")
    st.subheader("Resources")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **APIs and Data Sources:**
        - [Alpha Vantage API](https://www.alphavantage.co/)
        - [News API](https://newsapi.org/)
        - [Yahoo Finance RSS](https://finance.yahoo.com/)
        """)
    
    with col2:
        st.markdown("""
        **Models and Documentation:**
        - [FinBERT Model](https://huggingface.co/ProsusAI/finbert)
        - [Google Gemini API](https://ai.google/)
        - [Streamlit Documentation](https://docs.streamlit.io/)
        """)

def display_feedback_section():
    """Display the feedback section on the main page"""
    st.markdown("---")
    st.subheader("Feedback")
    st.markdown("We value your feedback! Please share your thoughts or feature requests:")
    
    feedback = st.text_area("Share your feedback or feature requests", height=100)
    if st.button("Submit Feedback"):
        if feedback:
            st.success("Thank you for your feedback! We appreciate your input.")
            # In a real app, you would save this feedback to a database
        else:
            st.warning("Please enter feedback before submitting.")
    
    # Add version info below feedback section
    st.markdown("---")
    st.markdown("**Version:** 1.0.0 | **Last Updated:** May 2025")

def create_comprehensive_export_data(stock_data, start_date, end_date):
    """Create comprehensive export data with all analysis results"""
    export_data = []
    
    for ticker in stock_data.keys():
        data = stock_data[ticker]
        
        # Initialize row with all possible fields
        row = {
            # Basic Info
            'Ticker': ticker,
            'Company_Name': '',
            'Analysis_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Date_Range_Start': start_date,
            'Date_Range_End': end_date,
            'Investing_Type': st.session_state.get('investing_type', 'N/A'),
            
            # Price Data
            'Latest_Close_Price': '',
            'Daily_Change_Percent': '',
            'Daily_Change_Amount': '',
            '52_Week_High': '',
            '52_Week_Low': '',
            '52_Week_Range': '',
            
            # Technical Analysis
            'Technical_Prediction': '',
            'Technical_Analysis': '',
            
            # Fundamental Analysis
            'Fundamental_Score': '',
            'PE_Ratio': '',
            'PB_Ratio': '',
            'ROE': '',
            'Current_Ratio': '',
            'Debt_to_Equity': '',
            'Market_Cap': '',
            'Revenue_Per_Share': '',
            'EPS': '',
            'Dividend_Yield': '',
            'Fundamental_Analysis_Description': '',
            
            # Sentiment Analysis
            'Sentiment_Score': '',
            'Sentiment_Label': '',
            'Articles_Analyzed': '',
            'Sentiment_Keyword_Used': '',
            'Article_Headlines': '',
            'News_Sources_Used': '',
            'Sentiment_Analysis_Description': '',
            
            # Combined Analysis
            'Combined_Prediction': '',
            'Combined_Score': '',
            'Technical_Weight': '',
            'Fundamental_Weight': '',
            'Sentiment_Weight': '',
            'Combined_Analysis_Summary': '',
            
            # Technical Indicators
            'Indicators_Used': '',
            'SMA_20_Latest': '',
            'EMA_20_Latest': '',
            'VWAP_Latest': '',
            'Bollinger_Upper': '',
            'Bollinger_Lower': '',
        }
        
        # Fill in data that exists
        if not data.empty:
            # Price data
            latest_close = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2] if len(data) > 1 else None
            daily_change_percent = ((latest_close - prev_close) / prev_close * 100) if prev_close else None
            daily_change_amount = (latest_close - prev_close) if prev_close else None
            
            row.update({
                'Latest_Close_Price': f"{latest_close:.2f}",
                'Daily_Change_Percent': f"{daily_change_percent:.2f}%" if daily_change_percent else "N/A",
                'Daily_Change_Amount': f"{daily_change_amount:.2f}" if daily_change_amount else "N/A",
                '52_Week_High': f"{data['High'].max():.2f}",
                '52_Week_Low': f"{data['Low'].min():.2f}",
                '52_Week_Range': f"{data['Low'].min():.2f} - {data['High'].max():.2f}",
            })
            
            # Technical indicators
            sma_20 = data['Close'].rolling(window=20).mean().iloc[-1] if len(data) >= 20 else None
            ema_20 = data['Close'].ewm(span=20).mean().iloc[-1] if len(data) >= 20 else None
            
            if sma_20 is not None:
                row['SMA_20_Latest'] = f"{sma_20:.2f}"
            if ema_20 is not None:
                row['EMA_20_Latest'] = f"{ema_20:.2f}"
            
            # Calculate VWAP if possible
            if 'Volume' in data.columns:
                data_copy = data.copy()
                data_copy['VWAP'] = (data_copy['Close'] * data_copy['Volume']).cumsum() / data_copy['Volume'].cumsum()
                vwap_latest = data_copy['VWAP'].iloc[-1]
                row['VWAP_Latest'] = f"{vwap_latest:.2f}"
            
            # Bollinger Bands
            if len(data) >= 20:
                sma = data['Close'].rolling(window=20).mean()
                std = data['Close'].rolling(window=20).std()
                bb_upper = (sma + 2 * std).iloc[-1]
                bb_lower = (sma - 2 * std).iloc[-1]
                row['Bollinger_Upper'] = f"{bb_upper:.2f}"
                row['Bollinger_Lower'] = f"{bb_lower:.2f}"
        
        # Get company name if available
        from sentiment import get_company_name
        company_name = get_company_name(ticker)
        if company_name:
            row['Company_Name'] = company_name
        
        # Get technical analysis results from session state
        if "analysis_results" in st.session_state and ticker in st.session_state["analysis_results"]:
            analysis = st.session_state["analysis_results"][ticker]
            row['Technical_Prediction'] = analysis.get("action", "")
            row['Technical_Analysis'] = analysis.get("justification", "")
        
        # Get fundamental analysis results
        if f"fundamental_results_{ticker}" in st.session_state:
            fundamental = st.session_state[f"fundamental_results_{ticker}"]
            row.update({
                'Fundamental_Score': str(fundamental.get('score', '')),
                'PE_Ratio': fundamental.get('essential_ratios', {}).get('P/E Ratio', ''),
                'PB_Ratio': fundamental.get('essential_ratios', {}).get('P/B Ratio', ''),
                'ROE': fundamental.get('essential_ratios', {}).get('ROE', ''),
                'Current_Ratio': fundamental.get('essential_ratios', {}).get('Current Ratio', ''),
                'Debt_to_Equity': fundamental.get('essential_ratios', {}).get('Debt-to-Equity', ''),
                'Market_Cap': fundamental.get('essential_ratios', {}).get('Market Cap', ''),
                'Revenue_Per_Share': fundamental.get('growth_metrics', {}).get('Revenue Per Share', ''),
                'EPS': fundamental.get('growth_metrics', {}).get('EPS Growth', ''),
                'Dividend_Yield': fundamental.get('growth_metrics', {}).get('Dividend Yield', ''),
                'Fundamental_Analysis_Description': fundamental.get('explanation', ''),
            })
        
        # Get sentiment analysis results
        if f"sentiment_results_{ticker}" in st.session_state:
            sentiment = st.session_state[f"sentiment_results_{ticker}"]
            if "error" not in sentiment:
                row.update({
                    'Sentiment_Score': f"{sentiment.get('score', 0):.2f}",
                    'Sentiment_Label': sentiment.get('sentiment', ''),
                    'Articles_Analyzed': str(sentiment.get('articles_analyzed', 0)),
                    'Sentiment_Keyword_Used': sentiment.get('keyword_used', ''),
                    'News_Sources_Used': ', '.join(sentiment.get('sources_used', [])),
                })
                
                # Create sentiment description
                sentiment_desc = f"Based on analysis of {sentiment.get('articles_analyzed', 0)} articles, " \
                               f"the sentiment is {sentiment.get('sentiment', 'N/A')} with a score of " \
                               f"{sentiment.get('score', 0):.2f}."
                row['Sentiment_Analysis_Description'] = sentiment_desc
                
                # Compile article headlines
                articles = sentiment.get('sample_articles', [])
                if articles:
                    headlines = [article.get('headline', '') for article in articles]
                    row['Article_Headlines'] = ' | '.join(headlines)
        
        # Get combined analysis results
        if "combined_results" in st.session_state and ticker in st.session_state["combined_results"]:
            combined = st.session_state["combined_results"][ticker]
            weights = combined.get('weights_used', {})
            row.update({
                'Combined_Prediction': combined.get('prediction', ''),
                'Combined_Score': f"{combined.get('score', 0):.3f}",
                'Technical_Weight': f"{weights.get('technical', 0)}%",
                'Fundamental_Weight': f"{weights.get('fundamental', 0)}%",
                'Sentiment_Weight': f"{weights.get('sentiment', 0)}%",
                'Combined_Analysis_Summary': f"Combined prediction based on {combined.get('investing_type', 'N/A')} strategy",
            })
        
        # Get indicators used from session state
        if "indicators_used" in st.session_state:
            row['Indicators_Used'] = ', '.join(st.session_state["indicators_used"])
        
        export_data.append(row)
    
    return pd.DataFrame(export_data)

# ui_components.py - Modified display_export_options function

def display_export_options(stock_data, overall_results):
    """Display export options in the sidebar without triggering API requests"""
    import streamlit as st
    import pandas as pd
    import io
    from datetime import datetime
    
    # Don't even attempt to show export options if no data is available
    if not stock_data or len(overall_results) == 0:
        st.sidebar.info("Load stock data first to enable export options.")
        return
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Export Options")
    
    # Create columns for different export formats
    col1, col2, col3 = st.sidebar.columns(3)
    
    # Use pre-generated data for export - no calculations or API calls
    # Get data that's already in the session state
    start_date = st.session_state.get("start_date", "N/A")
    end_date = st.session_state.get("end_date", "N/A")
    
    # Add timestamp to filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"turingrose_analysis_{timestamp}"
    
    # Export data in different formats with specific buttons for each
    # CSV Export
    with col1:
        # Create the DataFrame once
        if "export_df" not in st.session_state:
            # Create a simple export DataFrame without API calls
            export_data = []
            for result in overall_results:
                ticker = result["Stock"]
                prediction = result["Prediction"]
                # Add basic info from existing session state
                combined_info = st.session_state.get("combined_results", {}).get(ticker, {})
                row = {
                    "Ticker": ticker,
                    "Analysis_Date": datetime.now().strftime('%Y-%m-%d'),
                    "Technical_Signal": st.session_state.get("analysis_results", {}).get(ticker, {}).get("action", "N/A"),
                    "Combined_Prediction": prediction,
                    "Combined_Score": combined_info.get("score", 0),
                    "Strategy": combined_info.get("investing_type", "N/A")
                }
                export_data.append(row)
            
            st.session_state["export_df"] = pd.DataFrame(export_data)
        
        # Use the cached DataFrame
        csv_data = st.session_state["export_df"].to_csv(index=False)
        st.download_button(
            label="CSV",
            data=csv_data,
            file_name=f"{filename_base}.csv",
            mime="text/csv",
            key="csv_download"
        )
    
    # Excel Export
    with col2:
        # Use the same cached DataFrame
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            st.session_state["export_df"].to_excel(writer, sheet_name='Analysis', index=False)
        
        st.download_button(
            label="Excel",
            data=buffer.getvalue(),
            file_name=f"{filename_base}.xlsx",
            mime="application/vnd.ms-excel",
            key="excel_download"
        )
    
    # JSON Export
    with col3:
        # Use the same cached DataFrame
        json_data = st.session_state["export_df"].to_json(orient="records")
        st.download_button(
            label="JSON",
            data=json_data,
            file_name=f"{filename_base}.json",
            mime="application/json",
            key="json_download"
        )
