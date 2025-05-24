# config.py - Configuration settings
import streamlit as st
import google.generativeai as genai

# API Keys
GOOGLE_API_KEY = "AIzaSyD2mJ94OSl1zZeAgOmvveYu5CAToo9X_Ag"
ALPHA_VANTAGE_API_KEY = "NLKISJ9TBY2KCC6D"
MODEL_NAME = 'gemini-2.0-flash'

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)
gen_model = genai.GenerativeModel(MODEL_NAME)

# Analysis weights for different strategies
ANALYSIS_WEIGHTS = {
    'Value investing': {'technical': 20, 'fundamental': 60, 'sentiment': 20},
    'Balanced Approach': {'technical': 35, 'fundamental': 45, 'sentiment': 20},
    'Day/Swing Trading': {'technical': 60, 'fundamental': 20, 'sentiment': 20}
}