# weighted_fundamental_analysis.py - Strategy-weighted fundamental analysis
import streamlit as st
import requests
import json
import random
import pandas as pd
import numpy as np
from config import ALPHA_VANTAGE_API_KEY, gen_model, FUNDAMENTAL_RATIO_WEIGHTS, GROWTH_METRICS_WEIGHTS

def get_financial_statements(ticker):
    """Get detailed financial statements from Alpha Vantage"""
    statements = {}
    
    # Income Statement
    try:
        income_url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(income_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'annualReports' in data and len(data['annualReports']) > 0:
                statements['income'] = data['annualReports'][0]
    except Exception as e:
        print(f"Income statement error: {e}")
    
    # Balance Sheet
    try:
        balance_url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(balance_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'annualReports' in data and len(data['annualReports']) > 0:
                statements['balance'] = data['annualReports'][0]
    except Exception as e:
        print(f"Balance sheet error: {e}")
    
    # Cash Flow
    try:
        cashflow_url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(cashflow_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'annualReports' in data and len(data['annualReports']) > 0:
                statements['cashflow'] = data['annualReports'][0]
    except Exception as e:
        print(f"Cash flow error: {e}")
    
    return statements

def calculate_financial_ratios(overview_data, statements):
    """Calculate financial ratios from available data"""
    ratios = {}
    
    try:
        def safe_float(value, default=None):
            try:
                if value and value != 'None' and value != 'N/A':
                    return float(str(value).replace(',', ''))
                return default
            except (ValueError, TypeError):
                return default
        
        # From Overview data
        market_cap = safe_float(overview_data.get('MarketCapitalization'))
        pe_ratio = safe_float(overview_data.get('PERatio'))
        pb_ratio = safe_float(overview_data.get('PriceToBookRatio'))
        eps = safe_float(overview_data.get('EPS'))
        book_value = safe_float(overview_data.get('BookValue'))
        dividend_yield = safe_float(overview_data.get('DividendYield'))
        
        # Calculate ratios from statements if available
        if 'income' in statements and 'balance' in statements:
            income = statements['income']
            balance = statements['balance']
            
            net_income = safe_float(income.get('netIncome'))
            total_revenue = safe_float(income.get('totalRevenue'))
            
            total_assets = safe_float(balance.get('totalAssets'))
            total_equity = safe_float(balance.get('totalShareholderEquity'))
            current_assets = safe_float(balance.get('totalCurrentAssets'))
            current_liabilities = safe_float(balance.get('totalCurrentLiabilities'))
            total_debt = safe_float(balance.get('shortTermDebt', 0)) + safe_float(balance.get('longTermDebt', 0))
            
            # Calculate key ratios
            if net_income and total_equity and total_equity > 0:
                ratios['ROE'] = (net_income / total_equity) * 100
            
            if current_assets and current_liabilities and current_liabilities > 0:
                ratios['Current_Ratio'] = current_assets / current_liabilities
            
            if total_debt is not None and total_equity and total_equity > 0:
                ratios['Debt_to_Equity'] = total_debt / total_equity
            
            if net_income and total_assets and total_assets > 0:
                ratios['ROA'] = (net_income / total_assets) * 100
            
            if net_income and total_revenue and total_revenue > 0:
                ratios['Profit_Margin'] = (net_income / total_revenue) * 100
        
        # Add Cash Flow ratios
        if 'cashflow' in statements:
            cashflow = statements['cashflow']
            operating_cashflow = safe_float(cashflow.get('operatingCashflow'))
            capex = safe_float(cashflow.get('capitalExpenditures'))
            
            if operating_cashflow and capex:
                ratios['Free_Cash_Flow'] = operating_cashflow - abs(capex)
        
        # Add overview ratios
        if pe_ratio:
            ratios['PE_Ratio'] = pe_ratio
        if pb_ratio:
            ratios['PB_Ratio'] = pb_ratio
        if dividend_yield:
            ratios['Dividend_Yield'] = dividend_yield
        if market_cap:
            ratios['Market_Cap'] = market_cap
        
    except Exception as e:
        print(f"Error calculating ratios: {e}")
    
    return ratios

def generate_strategy_demo_data(ticker, investing_type):
    """Generate demo data tailored to investment strategy"""
    random.seed(hash(ticker) % 10000)
    
    # Base profiles by strategy preference
    if investing_type == "Value Investing":
        base_profile = {
            'market_cap': 50000000000, 'pe': 12, 'pb': 1.2, 'roe': 18, 
            'current_ratio': 2.1, 'debt_equity': 0.3, 'profit_margin': 15, 
            'dividend_yield': 3.2, 'revenue_growth': 5
        }
    elif investing_type == "Growth Investing":
        base_profile = {
            'market_cap': 200000000000, 'pe': 35, 'pb': 8.5, 'roe': 25, 
            'current_ratio': 1.4, 'debt_equity': 0.1, 'profit_margin': 22, 
            'dividend_yield': 0.0, 'revenue_growth': 25
        }
    elif investing_type == "Swing Trading":
        base_profile = {
            'market_cap': 100000000000, 'pe': 22, 'roe': 16, 'current_ratio': 1.3,
            'debt_equity': 0.5, 'profit_margin': 12, 'dividend_yield': 1.5, 'revenue_growth': 8
        }
    else:  # Balanced Approach
        base_profile = {
            'market_cap': 150000000000, 'pe': 25, 'pb': 3.2, 'roe': 20, 
            'current_ratio': 1.6, 'debt_equity': 0.4, 'profit_margin': 18, 
            'dividend_yield': 1.8, 'revenue_growth': 12
        }
    
    # Add randomness
    return {
        'MarketCapitalization': str(int(base_profile['market_cap'] * random.uniform(0.7, 1.3))),
        'PERatio': str(round(base_profile['pe'] * random.uniform(0.8, 1.2), 2)),
        'PriceToBookRatio': str(round(base_profile.get('pb', 2.5) * random.uniform(0.8, 1.2), 2)),
        'ROE': str(round(base_profile['roe'] * random.uniform(0.9, 1.1), 2)),
        'CurrentRatio': str(round(base_profile['current_ratio'] * random.uniform(0.9, 1.1), 2)),
        'DebtToEquityRatio': str(round(base_profile['debt_equity'] * random.uniform(0.8, 1.2), 2)),
        'RevenuePerShareTTM': str(round(random.uniform(15, 45), 2)),
        'EPS': str(round(random.uniform(3, 12), 2)),
        'DividendYield': str(round(base_profile['dividend_yield'] * random.uniform(0.8, 1.2), 3)),
        'ProfitMargin': str(round(base_profile['profit_margin'] * random.uniform(0.9, 1.1), 2)),
        'FreeCashFlow': str(int(random.uniform(8000000000, 45000000000))),
        'EBITDA': str(int(random.uniform(15000000000, 80000000000)))
    }

@st.cache_data(ttl=3600)
def get_company_overview_enhanced(ticker, investing_type):
    """Enhanced company overview with strategy-based fallback"""
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'Symbol' in data and data.get('Symbol') == ticker:
                return data, True
            else:
                return generate_strategy_demo_data(ticker, investing_type), False
        else:
            return generate_strategy_demo_data(ticker, investing_type), False
    except Exception as e:
        return generate_strategy_demo_data(ticker, investing_type), False

def calculate_weighted_fundamental_score(overview_data, calculated_ratios, investing_type, is_real_data):
    """Calculate weighted fundamental score based on investment strategy"""
    
    def safe_float(value, default=0):
        try:
            if value and str(value) not in ['None', 'N/A', '']:
                return float(str(value).replace(',', ''))
            return default
        except (ValueError, TypeError):
            return default
    
    # Extract all available metrics
    all_metrics = {
        'PE_Ratio': safe_float(overview_data.get('PERatio')),
        'PB_Ratio': safe_float(overview_data.get('PriceToBookRatio')),
        'ROE': safe_float(calculated_ratios.get('ROE', overview_data.get('ROE'))),
        'Current_Ratio': safe_float(calculated_ratios.get('Current_Ratio', overview_data.get('CurrentRatio'))),
        'Debt_to_Equity': safe_float(calculated_ratios.get('Debt_to_Equity', overview_data.get('DebtToEquityRatio'))),
        'Profit_Margin': safe_float(calculated_ratios.get('Profit_Margin', overview_data.get('ProfitMargin'))),
        'Dividend_Yield': safe_float(overview_data.get('DividendYield')),
        'Market_Cap': safe_float(overview_data.get('MarketCapitalization')),
        'ROA': safe_float(calculated_ratios.get('ROA')),
        'Free_Cash_Flow': safe_float(calculated_ratios.get('Free_Cash_Flow', overview_data.get('FreeCashFlow'))),
        'Revenue_Per_Share': safe_float(overview_data.get('RevenuePerShareTTM')),
        'EPS': safe_float(overview_data.get('EPS'))
    }
    
    # Get strategy-specific weights
    ratio_weights = FUNDAMENTAL_RATIO_WEIGHTS.get(investing_type, {})
    growth_weights = GROWTH_METRICS_WEIGHTS.get(investing_type, {})
    
    # Calculate weighted scores for each category
    valuation_score = 0
    profitability_score = 0
    health_score = 0
    growth_score = 0
    income_score = 0
    
    total_weights = {'valuation': 0, 'profitability': 0, 'health': 0, 'growth': 0, 'income': 0}
    
    # Valuation metrics
    valuation_metrics = ['PE_Ratio', 'PB_Ratio', 'Market_Cap']
    for metric in valuation_metrics:
        if metric in all_metrics and all_metrics[metric] > 0:
            weight = ratio_weights.get(metric, 0.5)
            score = score_individual_metric(metric, all_metrics[metric], investing_type)
            valuation_score += score * weight
            total_weights['valuation'] += weight
    
    # Profitability metrics
    profitability_metrics = ['ROE', 'Profit_Margin', 'ROA']
    for metric in profitability_metrics:
        if metric in all_metrics and all_metrics[metric] > 0:
            weight = ratio_weights.get(metric, 0.5)
            score = score_individual_metric(metric, all_metrics[metric], investing_type)
            profitability_score += score * weight
            total_weights['profitability'] += weight
    
    # Financial health metrics
    health_metrics = ['Current_Ratio', 'Debt_to_Equity']
    for metric in health_metrics:
        if metric in all_metrics and all_metrics[metric] > 0:
            weight = ratio_weights.get(metric, 0.5)
            score = score_individual_metric(metric, all_metrics[metric], investing_type)
            health_score += score * weight
            total_weights['health'] += weight
    
    # Growth metrics
    growth_metrics_list = ['Revenue_Per_Share', 'EPS', 'Free_Cash_Flow']
    for metric in growth_metrics_list:
        if metric in all_metrics and all_metrics[metric] > 0:
            weight = growth_weights.get(metric, 0.5)
            score = score_individual_metric(metric, all_metrics[metric], investing_type)
            growth_score += score * weight
            total_weights['growth'] += weight
    
    # Income metrics
    income_metrics = ['Dividend_Yield']
    for metric in income_metrics:
        if metric in all_metrics:
            weight = ratio_weights.get(metric, 0.5)
            score = score_individual_metric(metric, all_metrics[metric], investing_type)
            income_score += score * weight
            total_weights['income'] += weight
    
    # Normalize scores
    normalized_scores = {}
    for category in total_weights:
        if total_weights[category] > 0:
            if category == 'valuation':
                normalized_scores[category] = valuation_score / total_weights[category]
            elif category == 'profitability':
                normalized_scores[category] = profitability_score / total_weights[category]
            elif category == 'health':
                normalized_scores[category] = health_score / total_weights[category]
            elif category == 'growth':
                normalized_scores[category] = growth_score / total_weights[category]
            elif category == 'income':
                normalized_scores[category] = income_score / total_weights[category]
        else:
            normalized_scores[category] = 50  # Neutral score if no data
    
    # Strategy-specific category weights
    category_weights = {
        'Value Investing': {'valuation': 0.3, 'profitability': 0.25, 'health': 0.25, 'growth': 0.1, 'income': 0.1},
        'Growth Investing': {'valuation': 0.15, 'profitability': 0.2, 'health': 0.2, 'growth': 0.4, 'income': 0.05},
        'Swing Trading': {'valuation': 0.2, 'profitability': 0.3, 'health': 0.3, 'growth': 0.15, 'income': 0.05},
        'Balanced Approach': {'valuation': 0.25, 'profitability': 0.25, 'health': 0.25, 'growth': 0.2, 'income': 0.05}
    }
    
    weights = category_weights.get(investing_type, category_weights['Balanced Approach'])
    
    # Calculate final weighted score
    final_score = 0
    for category, weight in weights.items():
        final_score += normalized_scores.get(category, 50) * weight
    
    # Generate explanation
    explanation = generate_weighted_explanation(investing_type, normalized_scores, all_metrics, is_real_data)
    
    return {"score": int(final_score), "explanation": explanation}

def score_individual_metric(metric_name, value, investing_type):
    """Score individual metrics based on strategy preferences"""
    
    if metric_name == 'PE_Ratio':
        if investing_type == 'Value Investing':
            return 100 if value < 15 else 80 if value < 20 else 50 if value < 25 else 20
        elif investing_type == 'Growth Investing':
            return 70 if value < 30 else 50 if value < 40 else 30  # Growth can handle higher P/E
        else:
            return 100 if 15 <= value <= 25 else 70 if value < 15 else 50 if value < 30 else 30
    
    elif metric_name == 'ROE':
        if investing_type == 'Value Investing':
            return 100 if value > 15 else 80 if value > 10 else 50 if value > 5 else 20
        elif investing_type == 'Growth Investing':
            return 100 if value > 20 else 80 if value > 15 else 60 if value > 10 else 30
        else:
            return 100 if value > 18 else 80 if value > 12 else 60 if value > 8 else 30
    
    elif metric_name == 'Current_Ratio':
        if investing_type in ['Value Investing', 'Swing Trading']:
            return 100 if 1.5 <= value <= 3.0 else 70 if value >= 1.2 else 30
        else:
            return 80 if value >= 1.2 else 50 if value >= 1.0 else 20
    
    elif metric_name == 'Debt_to_Equity':
        if investing_type == 'Value Investing':
            return 100 if value < 0.3 else 80 if value < 0.5 else 50 if value < 1.0 else 20
        elif investing_type == 'Growth Investing':
            return 90 if value < 0.2 else 70 if value < 0.5 else 50 if value < 1.0 else 30
        else:
            return 100 if value < 0.4 else 70 if value < 0.8 else 40 if value < 1.2 else 20
    
    elif metric_name == 'Dividend_Yield':
        if investing_type == 'Value Investing':
            return 100 if value > 3 else 80 if value > 2 else 60 if value > 1 else 40
        elif investing_type == 'Growth Investing':
            return 60 if value == 0 else 40 if value < 2 else 20  # Growth prefers reinvestment
        else:
            return 80 if 1 <= value <= 4 else 60 if value < 1 else 40
    
    elif metric_name in ['Revenue_Per_Share', 'EPS', 'Free_Cash_Flow']:
        if investing_type == 'Growth Investing':
            return 100 if value > 0 else 20  # Growth needs positive metrics
        else:
            return 80 if value > 0 else 40
    
    # Default scoring
    return 50

def generate_weighted_explanation(investing_type, scores, metrics, is_real_data):
    """Generate strategy-specific explanation"""
    
    explanation = f"**{investing_type} Analysis** ({'Real Data' if is_real_data else 'Demo Data'}):\n\n"
    
    if investing_type == 'Value Investing':
        explanation += f"**Valuation Focus** (Score: {scores.get('valuation', 50):.0f}/100): "
        if metrics['PE_Ratio'] > 0:
            explanation += f"P/E ratio of {metrics['PE_Ratio']:.1f} "
            explanation += "suggests good value" if metrics['PE_Ratio'] < 20 else "indicates premium pricing"
        
        explanation += f"\n**Financial Strength** (Score: {scores.get('health', 50):.0f}/100): "
        if metrics['Current_Ratio'] > 0:
            explanation += f"Current ratio of {metrics['Current_Ratio']:.2f} "
            explanation += "shows strong liquidity" if metrics['Current_Ratio'] > 1.5 else "indicates tight liquidity"
        
        explanation += f"\n**Income Generation** (Score: {scores.get('income', 50):.0f}/100): "
        explanation += f"Dividend yield of {metrics['Dividend_Yield']:.2f}% "
        explanation += "provides attractive income" if metrics['Dividend_Yield'] > 2 else "offers limited income"
    
    elif investing_type == 'Growth Investing':
        explanation += f"**Growth Potential** (Score: {scores.get('growth', 50):.0f}/100): "
        explanation += "Strong growth metrics indicate expansion potential" if scores.get('growth', 50) > 70 else "Growth metrics suggest moderate expansion"
        
        explanation += f"\n**Profitability** (Score: {scores.get('profitability', 50):.0f}/100): "
        if metrics['ROE'] > 0:
            explanation += f"ROE of {metrics['ROE']:.1f}% "
            explanation += "demonstrates excellent management efficiency" if metrics['ROE'] > 20 else "shows adequate profitability"
        
        explanation += f"\n**Financial Flexibility** (Score: {scores.get('health', 50):.0f}/100): "
        if metrics['Debt_to_Equity'] >= 0:
            explanation += f"Debt-to-equity of {metrics['Debt_to_Equity']:.2f} "
            explanation += "provides financial flexibility for growth" if metrics['Debt_to_Equity'] < 0.5 else "may limit growth investments"
    
    elif investing_type == 'Swing Trading':
        explanation += f"**Financial Stability** (Score: {scores.get('health', 50):.0f}/100): "
        explanation += "Strong balance sheet reduces downside risk" if scores.get('health', 50) > 70 else "Balance sheet requires monitoring"
        
        explanation += f"\n**Profitability** (Score: {scores.get('profitability', 50):.0f}/100): "
        explanation += "Solid earnings support price momentum" if scores.get('profitability', 50) > 60 else "Earnings may limit upside potential"
        
        explanation += f"\n**Valuation** (Score: {scores.get('valuation', 50):.0f}/100): "
        explanation += "Reasonable valuation supports swing trades" if scores.get('valuation', 50) > 60 else "High valuation increases risk"
    
    else:  # Balanced Approach
        explanation += f"**Overall Balance** - Valuation: {scores.get('valuation', 50):.0f}/100. "
        explanation += f"Profitability: {scores.get('profitability', 50):.0f}/100. "
        explanation += f"Health: {scores.get('health', 50):.0f}/100. "
        explanation += f"Growth: {scores.get('growth', 50):.0f}/100. "
        
        avg_score = sum(scores.values()) / len(scores)
        if avg_score > 70:
            explanation += "Well-rounded investment opportunity with strong fundamentals across multiple areas."
        elif avg_score > 50:
            explanation += "Decent investment with some strengths but areas for improvement."
        else:
            explanation += "Faces challenges in multiple fundamental areas requiring careful consideration."
    
    return explanation

@st.cache_data(ttl=3600)
def analyze_fundamentals_weighted(ticker, investing_type, use_demo=False):
    """Main function for strategy-weighted fundamental analysis"""
    
    if use_demo:
        overview_data = generate_strategy_demo_data(ticker, investing_type)
        calculated_ratios = {}
        is_real_data = False
    else:
        overview_data, is_real_data = get_company_overview_enhanced(ticker, investing_type)
        statements = get_financial_statements(ticker) if is_real_data else {}
        calculated_ratios = calculate_financial_ratios(overview_data, statements) if statements else {}
    
    # Calculate weighted score
    analysis_result = calculate_weighted_fundamental_score(overview_data, calculated_ratios, investing_type, is_real_data)
    
    # Prepare display ratios
    def get_best_value(calc_key, overview_key, format_func=lambda x: f"{x:.2f}"):
        calc_val = calculated_ratios.get(calc_key)
        overview_val = overview_data.get(overview_key)
        
        if calc_val is not None:
            return format_func(calc_val) + " ✓"
        elif overview_val and overview_val != 'None':
            try:
                return format_func(float(overview_val))
            except:
                return str(overview_val)
        else:
            return "N/A"
    
    essential_ratios = {
        'P/E Ratio': overview_data.get('PERatio', 'N/A'),
        'P/B Ratio': overview_data.get('PriceToBookRatio', 'N/A'),
        'ROE': get_best_value('ROE', 'ROE', lambda x: f"{x:.1f}%"),
        'Current Ratio': get_best_value('Current_Ratio', 'CurrentRatio'),
        'Debt-to-Equity': get_best_value('Debt_to_Equity', 'DebtToEquityRatio'),
        'Market Cap': f"${float(overview_data.get('MarketCapitalization', 0)):,.0f}" if overview_data.get('MarketCapitalization') else 'N/A'
    }
    
    growth_metrics = {
        'Revenue Per Share': f"${overview_data.get('RevenuePerShareTTM', 'N/A')}",
        'EPS': overview_data.get('EPS', 'N/A'),
        'Dividend Yield': f"{overview_data.get('DividendYield', 'N/A')}%",
        'Free Cash Flow': f"${calculated_ratios.get('Free_Cash_Flow', 'N/A'):,.0f}" if calculated_ratios.get('Free_Cash_Flow') else overview_data.get('FreeCashFlow', 'N/A'),
        'Profit Margin': get_best_value('Profit_Margin', 'ProfitMargin', lambda x: f"{x:.1f}%")
    }
    
    return {
        'score': analysis_result['score'],
        'explanation': analysis_result['explanation'],
        'essential_ratios': essential_ratios,
        'growth_metrics': growth_metrics,
        'data_source': 'Real Data' if is_real_data else 'Demo Data',
        'strategy_weighted': True,
        'investing_type': investing_type
    }