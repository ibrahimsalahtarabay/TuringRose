# test_news_api.py - Test script to verify News API is working

import requests
from datetime import datetime, timedelta

# Your API key
API_KEY = "4ec0f470acd040198a8c31ef4bb0a2c9"

# Test the API
def test_news_api():
    # Get yesterday's date for testing
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    url = (
        'https://newsapi.org/v2/everything?'
        'q=Apple&'
        f'from={yesterday}&'
        'sortBy=popularity&'
        f'apiKey={API_KEY}'
    )
    
    print(f"Testing News API with URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! API is working.")
            print(f"Total articles found: {data.get('totalResults', 0)}")
            print(f"Articles returned: {len(data.get('articles', []))}")
            
            # Show first article as example
            if data.get('articles'):
                first_article = data['articles'][0]
                print("\nFirst article:")
                print(f"Title: {first_article.get('title', 'N/A')}")
                print(f"Description: {first_article.get('description', 'N/A')}")
                print(f"URL: {first_article.get('url', 'N/A')}")
        
        elif response.status_code == 400:
            print("❌ Error 400: Bad Request - Check your query parameters")
            print(f"Response: {response.text}")
        
        elif response.status_code == 401:
            print("❌ Error 401: Unauthorized - Invalid API key")
            print("Please check your API key")
        
        elif response.status_code == 426:
            print("❌ Error 426: Upgrade Required")
            print("Your account may need upgrading or you've hit rate limits")
            print(f"Response: {response.text}")
        
        elif response.status_code == 429:
            print("❌ Error 429: Too Many Requests")
            print("You've hit the rate limit. Wait and try again.")
        
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    test_news_api()