# sentiment.py - Sentiment analysis
import streamlit as st
import numpy as np
import feedparser
from datetime import datetime

def get_company_name(ticker):
    """Map stock ticker to company name"""
    company_map = {
        'AAPL': 'Apple', 'MSFT': 'Microsoft', 'GOOG': 'Google', 'GOOGL': 'Google',
        'AMZN': 'Amazon', 'META': 'Meta', 'FB': 'Facebook', 'TSLA': 'Tesla',
        'NVDA': 'NVIDIA', 'JPM': 'JPMorgan Chase', 'V': 'Visa', 'JNJ': 'Johnson & Johnson',
        'WMT': 'Walmart', 'PG': 'Procter & Gamble', 'MA': 'Mastercard',
        'UNH': 'UnitedHealth Group', 'HD': 'Home Depot', 'BAC': 'Bank of America',
        'XOM': 'Exxon Mobil', 'DIS': 'Disney'
    }
    return company_map.get(ticker, None)

@st.cache_data(ttl=3600)
def analyze_sentiment(ticker, start_date, end_date, api_key=None, use_demo=False):
    """Analyze sentiment from news articles and RSS feeds"""
    company_name = get_company_name(ticker)
    keyword = company_name if company_name else ticker
    
    try:
        from transformers import pipeline
        transformers_available = True
    except ImportError:
        st.warning("⚠️ Transformers library not properly installed. Using demo sentiment data.")
        transformers_available = False
        use_demo = True
    
    # Demo mode
    if use_demo or not transformers_available:
        np.random.seed(hash(ticker) % 10000)
        sentiment_score = np.random.normal(0.2, 0.3)
        articles_found = np.random.randint(10, 30)
        
        sample_headlines = [
            f"{keyword} reports strong quarterly earnings",
            f"Analysts upgrade {keyword} to 'buy' rating",
            f"New product from {keyword} receives mixed reviews",
            f"{keyword} faces supply chain challenges",
            f"Investors bullish on {keyword}'s growth potential"
        ]
        
        sample_sentiments = [
            {"headline": sample_headlines[0], "sentiment": "positive", "score": 0.85},
            {"headline": sample_headlines[1], "sentiment": "positive", "score": 0.76},
            {"headline": sample_headlines[2], "sentiment": "neutral", "score": 0.12},
            {"headline": sample_headlines[3], "sentiment": "negative", "score": -0.45},
            {"headline": sample_headlines[4], "sentiment": "positive", "score": 0.65}
        ]
        
        return {
            "score": sentiment_score,
            "sentiment": "Positive" if sentiment_score > 0.15 else "Negative" if sentiment_score < -0.15 else "Neutral",
            "articles_analyzed": articles_found,
            "sample_articles": sample_sentiments,
            "keyword_used": keyword,
            "date_range": f"{start_date} to {end_date}"
        }
    
    # Real analysis
    try:
        pipe = pipeline(task="text-classification", model="ProsusAI/finbert")
        
        total_score = 0
        num_articles = 0
        analyzed_articles = []
        
        start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
        end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else end_date
        
        # Yahoo Finance RSS feed
        rss_url = f'https://finance.yahoo.com/rss/headline?s={ticker}'
        try:
            feed = feedparser.parse(rss_url)
            
            if feed.entries:
                for entry in feed.entries[:10]:
                    if (keyword.lower() not in entry.summary.lower() and 
                        keyword.lower() not in entry.title.lower() and
                        ticker.lower() not in entry.summary.lower() and
                        ticker.lower() not in entry.title.lower()):
                        continue
                        
                    sentiment_result = pipe(entry.summary)[0]
                    sentiment_label = sentiment_result['label']
                    sentiment_score = sentiment_result['score']
                    
                    if sentiment_label == 'positive':
                        total_score += sentiment_score
                        num_articles += 1
                    elif sentiment_label == 'negative':
                        total_score -= sentiment_score
                        num_articles += 1
                    elif sentiment_label == 'neutral':
                        num_articles += 1
                        
                    analyzed_articles.append({
                        "headline": entry.title,
                        "sentiment": sentiment_label,
                        "score": sentiment_score if sentiment_label != 'negative' else -sentiment_score,
                        "source": "Yahoo Finance RSS"
                    })
                
        except Exception as e:
            st.warning(f"Error fetching from Yahoo Finance RSS: {e}")
            
        if num_articles > 0:
            final_score = total_score / num_articles
            sentiment_label = "Positive" if final_score > 0.15 else "Negative" if final_score < -0.15 else "Neutral"
            
            analyzed_articles.sort(key=lambda x: abs(x["score"]), reverse=True)
            
            return {
                "score": final_score,
                "sentiment": sentiment_label,
                "articles_analyzed": num_articles,
                "sample_articles": analyzed_articles[:5],
                "keyword_used": keyword,
                "date_range": f"{start_str} to {end_str}",
                "sources_used": list(set([article.get("source", "Unknown") for article in analyzed_articles]))
            }
        else:
            st.warning(f"No articles found for {keyword}. Using demo sentiment data.")
            return analyze_sentiment(ticker, start_date, end_date, api_key=None, use_demo=True)
            
    except Exception as e:
        st.error(f"Sentiment analysis failed: {e}")
        return analyze_sentiment(ticker, start_date, end_date, api_key=None, use_demo=True)