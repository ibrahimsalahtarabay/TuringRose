# sentiment.py - Sentiment analysis functions (with dynamic keyword and date range)
import streamlit as st
import numpy as np
import requests
import feedparser
from datetime import datetime

def get_company_name(ticker):
    """Map stock ticker to company name"""
    company_map = {
        'AAPL': 'Apple',
        'MSFT': 'Microsoft',
        'GOOG': 'Google',
        'GOOGL': 'Google',
        'AMZN': 'Amazon',
        'META': 'Meta',
        'FB': 'Facebook',
        'TSLA': 'Tesla',
        'NVDA': 'NVIDIA',
        'JPM': 'JPMorgan Chase',
        'V': 'Visa',
        'JNJ': 'Johnson & Johnson',
        'WMT': 'Walmart',
        'PG': 'Procter & Gamble',
        'MA': 'Mastercard',
        'UNH': 'UnitedHealth Group',
        'HD': 'Home Depot',
        'BAC': 'Bank of America',
        'XOM': 'Exxon Mobil',
        'DIS': 'Disney'
    }
    return company_map.get(ticker, None)

@st.cache_data(ttl=3600)  # Cache data for 1 hour to reduce API calls
def analyze_sentiment(ticker, start_date, end_date, api_key=None, use_demo=False):
    """
    Analyze sentiment from news articles and RSS feeds for a stock ticker
    Uses the company name as keyword and the same date range as technical analysis
    """
    
    # Generate keyword based on ticker - use company name if available, otherwise ticker
    company_name = get_company_name(ticker)
    keyword = company_name if company_name else ticker
    
    # Try to import transformers, fallback to demo mode if it fails
    try:
        from transformers import pipeline
        transformers_available = True
    except ImportError:
        st.warning("⚠️ Transformers library not properly installed. Using demo sentiment data.")
        transformers_available = False
        use_demo = True
    
    # If using demo mode, return simulated sentiment
    if use_demo or not transformers_available:
        # Generate a simulated sentiment score
        np.random.seed(hash(ticker) % 10000)  # Seed based on ticker for consistency
        sentiment_score = np.random.normal(0.2, 0.3)  # Slightly positive bias
        articles_found = np.random.randint(10, 30)
        
        # Sample articles with sentiment
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
        
        # Return demo sentiment data
        return {
            "score": sentiment_score,
            "sentiment": "Positive" if sentiment_score > 0.15 else "Negative" if sentiment_score < -0.15 else "Neutral",
            "articles_analyzed": articles_found,
            "sample_articles": sample_sentiments,
            "keyword_used": keyword,
            "date_range": f"{start_date} to {end_date}"
        }
    
    # If not demo mode, perform actual sentiment analysis
    try:
        # Load finbert model for sentiment analysis
        try:
            pipe = pipeline(task="text-classification", model="ProsusAI/finbert")
        except Exception as e:
            st.error(f"Failed to load the sentiment model: {e}")
            return {"error": "Failed to load sentiment model"}
        
        # Initialize variables for sentiment calculation
        total_score = 0
        num_articles = 0
        analyzed_articles = []
        
        # Format dates for API (use technical analysis date range)
        if isinstance(start_date, datetime):
            start_str = start_date.strftime('%Y-%m-%d')
        else:
            start_str = start_date
            
        if isinstance(end_date, datetime):
            end_str = end_date.strftime('%Y-%m-%d')
        else:
            end_str = end_date
        
        # NewsAPI is commented out due to limitations - using Yahoo Finance RSS only
        # First source: NewsAPI (with error handling)
        # if api_key:
        #     # Use both company name and ticker as search queries for better coverage
        #     search_queries = [keyword]
        #     if keyword != ticker:
        #         search_queries.append(ticker)
        #     
        #     for query in search_queries:
        #         url = (
        #             'https://newsapi.org/v2/everything?'
        #             f'q={query}&'
        #             f'from={start_str}&'
        #             'sortBy=popularity&'
        #             f'apiKey={api_key}'
        #         )
        #         
        #         try:
        #             response = requests.get(url)
        #             
        #             if response.status_code == 200 and 'articles' in response.json():
        #                 data = response.json()
        #                 articles = data['articles']
        #                 # Filter articles that contain the keyword in title or description
        #                 articles = [
        #                     article for article in articles 
        #                     if (query.lower() in article['title'].lower() or 
        #                         (article['description'] and query.lower() in article['description'].lower()))
        #                 ]
        #                 
        #                 # Analyze sentiment for each article
        #                 for article in articles[:10]:  # Limit to 10 articles per query
        #                     # Use title + description for sentiment analysis
        #                     content = article['title']
        #                     if article['description']:
        #                         content += " " + article['description']
        #                         
        #                     sentiment_result = pipe(content)[0]
        #                     sentiment_label = sentiment_result['label']
        #                     sentiment_score = sentiment_result['score']
        #                     
        #                     # Add to total score based on sentiment
        #                     if sentiment_label == 'positive':
        #                         total_score += sentiment_score
        #                         num_articles += 1
        #                     elif sentiment_label == 'negative':
        #                         total_score -= sentiment_score
        #                         num_articles += 1
        #                     elif sentiment_label == 'neutral':
        #                         num_articles += 1
        #                         
        #                     # Save article info
        #                     analyzed_articles.append({
        #                         "headline": article['title'],
        #                         "sentiment": sentiment_label,
        #                         "score": sentiment_score if sentiment_label != 'negative' else -sentiment_score,
        #                         "source": "News API"
        #                     })
        #             elif response.status_code == 426:
        #                 st.warning("⚠️ News API upgrade required (Status 426).")
        #             elif response.status_code == 429:
        #                 st.warning("⚠️ News API rate limit exceeded.")
        #             elif response.status_code == 401:
        #                 st.warning("⚠️ Invalid News API key.")
        #             else:
        #                 st.warning(f"News API returned status code {response.status_code} for query '{query}'.")
        #         except Exception as e:
        #             st.warning(f"Error fetching from News API for '{query}': {e}")
        # else:
        #     st.info("No valid News API key provided. Using Yahoo Finance RSS feeds only.")
        
        # Using Yahoo Finance RSS feed (as primary source now)
        rss_url = f'https://finance.yahoo.com/rss/headline?s={ticker}'
        try:
            feed = feedparser.parse(rss_url)
            
            if feed.entries:
                # Analyze sentiment for each RSS entry
                for entry in feed.entries[:10]:  # Limit to 10 entries
                    # Check if keyword is in the entry summary
                    if (keyword.lower() not in entry.summary.lower() and 
                        keyword.lower() not in entry.title.lower() and
                        ticker.lower() not in entry.summary.lower() and
                        ticker.lower() not in entry.title.lower()):
                        continue
                        
                    sentiment_result = pipe(entry.summary)[0]
                    sentiment_label = sentiment_result['label']
                    sentiment_score = sentiment_result['score']
                    
                    # Add to total score based on sentiment
                    if sentiment_label == 'positive':
                        total_score += sentiment_score
                        num_articles += 1
                    elif sentiment_label == 'negative':
                        total_score -= sentiment_score
                        num_articles += 1
                    elif sentiment_label == 'neutral':
                        num_articles += 1
                        
                    # Save article info
                    analyzed_articles.append({
                        "headline": entry.title,
                        "sentiment": sentiment_label,
                        "score": sentiment_score if sentiment_label != 'negative' else -sentiment_score,
                        "source": "Yahoo Finance RSS"
                    })
                
        except Exception as e:
            st.warning(f"Error fetching from Yahoo Finance RSS: {e}")
            
        # Calculate final sentiment score
        if num_articles > 0:
            final_score = total_score / num_articles
            sentiment_label = "Positive" if final_score > 0.15 else "Negative" if final_score < -0.15 else "Neutral"
            
            # Sort articles by absolute score (strongest sentiment first)
            analyzed_articles.sort(key=lambda x: abs(x["score"]), reverse=True)
            
            return {
                "score": final_score,
                "sentiment": sentiment_label,
                "articles_analyzed": num_articles,
                "sample_articles": analyzed_articles[:5],  # Return top 5 articles with strongest sentiment
                "keyword_used": keyword,
                "date_range": f"{start_str} to {end_str}",
                "sources_used": list(set([article.get("source", "Unknown") for article in analyzed_articles]))
            }
        else:
            # If no articles found, fall back to demo data
            st.warning(f"No articles found for {keyword} in the specified date range. Using demo sentiment data.")
            return analyze_sentiment(ticker, start_date, end_date, api_key=None, use_demo=True)
            
    except Exception as e:
        st.error(f"Sentiment analysis failed: {e}")
        # Fall back to demo data on any error
        return analyze_sentiment(ticker, start_date, end_date, api_key=None, use_demo=True)

# Additional sentiment analysis helper functions
def get_sentiment_color(sentiment):
    """Return a color based on sentiment"""
    color_map = {
        "Positive": "lightgreen",
        "Negative": "salmon",
        "Neutral": "gold"
    }
    return color_map.get(sentiment, "gray")

def categorize_sentiment(score):
    """Categorize a sentiment score into Positive, Negative, or Neutral"""
    if score > 0.15:
        return "Positive"
    elif score < -0.15:
        return "Negative"
    else:
        return "Neutral"