# AI-Powered Technical Stock Analysis Dashboard

A Streamlit application for analyzing stocks using technical indicators and AI-powered insights, with sentiment analysis from news sources.

## Features

- **Technical Analysis**: View candlestick charts with various technical indicators (SMA, EMA, Bollinger Bands, VWAP)
- **AI Analysis**: Get AI-powered recommendations based on chart patterns
- **Sentiment Analysis**: Analyze sentiment from news articles and social media about stocks
- **Combined Insights**: View recommendations that combine technical and sentiment analysis
- **Export Options**: Export analysis results in CSV, Excel, or JSON formats

## Project Structure

The application is organized into several modules:

- `app.py`: Main application file that orchestrates the UI and logic
- `config.py`: Configuration settings for the app (API keys, model settings)
- `data_handler.py`: Functions for fetching and processing stock data
- `analysis.py`: Technical analysis functions using the AI model
- `sentiment.py`: Sentiment analysis of news and social media
- `ui_components.py`: Reusable UI components for Streamlit

## Installation and Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/stock-analysis-dashboard.git
   cd stock-analysis-dashboard
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up API keys:
   - Get a Google API key for the Gemini model
   - Get an Alpha Vantage API key for stock data
   - (Optional) Get a News API key for better sentiment analysis
   - Edit `config.py` with your API keys

4. Run the application:
   ```
   streamlit run app.py
   ```

## Usage

1. Enter stock ticker symbols (comma-separated)
2. Select date range and technical indicators
3. Enable sentiment analysis if desired
4. Click "Fetch Data" to load and analyze stocks
5. View analysis in the tabs for each stock
6. Export results using the sidebar

## Dependencies

- Streamlit: Web application framework
- Pandas/NumPy: Data processing
- Plotly: Interactive charts
- Google Generative AI: AI model for technical analysis
- Alpha Vantage: Stock market data API
- Transformers: Sentiment analysis with FinBERT
- Requests/Feedparser: News and social media data fetching

## API Keys

The application requires the following API keys:

- **Google API Key**: For the Gemini model (technical analysis)
- **Alpha Vantage API Key**: For stock market data
- **News API Key** (optional): For better sentiment analysis