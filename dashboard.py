import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta
import json
from fpdf import FPDF

st.set_page_config(layout="wide", page_title="Market Analysis Dashboard")

# --- SESSION STATE ---
if 'page' not in st.session_state:
    st.session_state.page = 'overview'
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []
if 'watchlist_search' not in st.session_state:
    st.session_state.watchlist_search = ""

# --- TOP 10 S&P 500 STOCKS FOR HEAT MAP ---
HEATMAP_STOCKS = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'GOOGL', 'TSLA', 'JPM', 'VZ', 'KO']

# --- ALL STOCKS: Top 10 per sector (110 stocks) ---
ALL_STOCKS = [
    "AAPL", "MSFT", "NVDA", "AVGO", "ADBE", "CRM", "CSCO", "ACN", "TXN", "INTU",
    "UNH", "LLY", "JNJ", "MRK", "ABBV", "TMO", "PFE", "DHR", "AMGN", "BMY",
    "JPM", "BAC", "WFC", "MS", "GS", "AXP", "SPGI", "BLK", "SCHW", "CME",
    "AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "TGT",
    "GOOGL", "GOOG", "META", "NFLX", "CMCSA", "VZ", "T", "DIS", "CHTR", "TMUS",
    "CAT", "UNP", "HON", "LMT", "UPS", "RTX", "BA", "GE", "DE", "NOC",
    "PG", "KO", "PEP", "WMT", "COST", "MDLZ", "CL", "KMB", "KR",
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "PXD", "VLO", "OXY",
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "ED", "PCG",
    "PLD", "AMT", "EQIX", "CCI", "PSA", "SPG", "O", "DLR", "WELL", "AVB",
    "LIN", "SHW", "FCX", "NEM", "DOW", "DD", "APD", "ECL", "IP", "ALB"
]

# --- CUSTOM CSS FOR DARK MODE ---
def get_css():
    if st.session_state.dark_mode:
        return """
            <style>
                .stApp { background-color: #1a1a2e; color: #e0e0e0; }
                .main-header { background-color: #16213e; border-bottom: 2px solid #0f3460; }
                .main-header h1 { color: #e0e0e0; }
                .main-header p { color: #a0a0b0; }
                .metric-card { background-color: #16213e; border: 1px solid #2a2a4e; box-shadow: 0 2px 8px rgba(0,0,0,0.3); }
                .metric-label { color: #a0a0b0; }
                .metric-value { color: #e0e0e0; }
                .card { background-color: #16213e; border: 1px solid #2a2a4e; }
                .section-header { color: #e0e0e0; border-bottom-color: #2a2a4e; }
                .whatif-card { background-color: #16213e; }
                .footer { border-top-color: #2a2a4e; color: #a0a0b0; }
                div[data-testid="stSelectbox"] label { color: #e0e0e0; }
                div[data-testid="stTextInput"] label { color: #e0e0e0; }
                .st-bw { background-color: #1a1a2e; }
                .st-ae { background-color: #16213e; }
                div[data-testid="stMetric"] { background-color: #16213e; padding: 10px; border-radius: 8px; border: 1px solid #2a2a4e; }
                div[data-testid="stMetric"] label { color: #a0a0b0; }
                div[data-testid="stMetric"] div { color: #e0e0e0; }
                div[data-testid="stMetric"] span { color: #e0e0e0; }
                .stTabs [data-baseweb="tab-list"] { background-color: #16213e; }
                .stTabs [data-baseweb="tab"] { color: #a0a0b0; }
                .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #e0e0e0; border-bottom-color: #ADD8E6; }
            </style>
        """
    else:
        return """
            <style>
                .stApp { background-color: #FFFFFF; }
                .main-header { background-color: #f8f9fa; border-bottom: 1px solid #e9ecef; }
                .main-header h1 { color: #1a1a2e; }
                .main-header p { color: #6c757d; }
                .metric-card { background-color: #f8f9fa; border: 1px solid #e9ecef; }
                .metric-label { color: #6c757d; }
                .metric-value { color: #1a1a2e; }
                .card { background-color: #ffffff; border: 1px solid #e9ecef; }
                .section-header { color: #1a1a2e; border-bottom-color: #e9ecef; }
                .whatif-card { background-color: #f8f9fa; }
                .footer { border-top-color: #e9ecef; color: #6c757d; }
                div[data-testid="stMetric"] { background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #e9ecef; }
            </style>
        """

# --- HELPER FUNCTIONS ---
def get_stock_data(ticker, period="1y", interval="1d"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        info = stock.info
        return hist, info
    except:
        return None, None

def get_indices():
    indices = {'DOW': '^DJI', 'NASDAQ': '^IXIC', 'S&P 500': '^GSPC', 'RUSSELL 2000': '^RUT'}
    result = {}
    for name, symbol in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1mo", interval="1d")
            if data is not None and not data.empty:
                result[name] = data
            else:
                result[name] = None
        except:
            result[name] = None
    return result

def get_daily_change(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="2d", interval="1d")
        if not data.empty and len(data) >= 2:
            current = float(data['Close'].iloc[-1])
            prev = float(data['Close'].iloc[-2])
            change = ((current - prev) / prev) * 100
            return change
    except:
        pass
    return 0.0

def get_vix_data():
    try:
        vix = yf.Ticker("^VIX")
        data = vix.history(period="1mo")
        if not data.empty:
            return data
    except:
        pass
    return None

def get_sp500_data():
    try:
        spy = yf.Ticker("SPY")
        data = spy.history(period="1y")
        if not data.empty:
            return data
    except:
        pass
    return None

def get_yahoo_news(ticker=None):
    try:
        if ticker:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}"
        else:
            url = "https://query1.finance.yahoo.com/v1/finance/search?q=stock%20market"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            news_items = []
            if 'news' in data:
                for item in data['news'][:10]:
                    news_items.append({
                        'title': item.get('title', 'No title'),
                        'link': item.get('link', '#'),
                        'publisher': item.get('publisher', 'Unknown'),
                    })
            return news_items
    except:
        pass
    return []

def create_candlestick_chart(data, title, height=300):
    if data is None or data.empty:
        return None
    try:
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close']
        )])
        bg_color = "#16213e" if st.session_state.dark_mode else "white"
        text_color = "#e0e0e0" if st.session_state.dark_mode else "#1a1a2e"
        grid_color = "#2a2a4e" if st.session_state.dark_mode else "#f0f0f0"
        fig.update_layout(
            title=title,
            height=height,
            template="plotly_white" if not st.session_state.dark_mode else "plotly_dark",
            showlegend=False,
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color,
            font_color=text_color
        )
        fig.update_xaxes(showgrid=True, gridcolor=grid_color)
        fig.update_yaxes(showgrid=True, gridcolor=grid_color)
        return fig
    except:
        return None

def create_vix_chart(data):
    if data is None or data.empty:
        return None
    try:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='VIX',
            line=dict(color='#FF6B6B', width=2)
        ))
        if len(data) >= 50:
            ma_50 = data['Close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(
                x=data.index,
                y=ma_50,
                mode='lines',
                name='50-Day MA',
                line=dict(color='#6C757D', width=1.5, dash='dash')
            ))
        bg_color = "#16213e" if st.session_state.dark_mode else "white"
        text_color = "#e0e0e0" if st.session_state.dark_mode else "#1a1a2e"
        grid_color = "#2a2a4e" if st.session_state.dark_mode else "#f0f0f0"
        fig.update_layout(
            title='VIX (Volatility Index)',
            height=300,
            template="plotly_white" if not st.session_state.dark_mode else "plotly_dark",
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color,
            font_color=text_color
        )
        fig.update_xaxes(showgrid=True, gridcolor=grid_color)
        fig.update_yaxes(showgrid=True, gridcolor=grid_color)
        return fig
    except:
        return None

def create_sp500_ma_chart(data):
    if data is None or data.empty:
        return None
    try:
        ma_125 = data['Close'].rolling(window=125).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='S&P 500',
            line=dict(color='#1A73E8', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=data.index,
            y=ma_125,
            mode='lines',
            name='125-Day MA',
            line=dict(color='#FF6B6B', width=2, dash='dash')
        ))
        bg_color = "#16213e" if st.session_state.dark_mode else "white"
        text_color = "#e0e0e0" if st.session_state.dark_mode else "#1a1a2e"
        grid_color = "#2a2a4e" if st.session_state.dark_mode else "#f0f0f0"
        fig.update_layout(
            title='S&P 500 vs 125-Day Moving Average',
            height=300,
            template="plotly_white" if not st.session_state.dark_mode else "plotly_dark",
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color,
            font_color=text_color
        )
        fig.update_xaxes(showgrid=True, gridcolor=grid_color)
        fig.update_yaxes(showgrid=True, gridcolor=grid_color)
        return fig
    except:
        return None

def create_bollinger_bands_chart(data):
    if data is None or data.empty:
        return None
    try:
        sma_20 = data['Close'].rolling(window=20).mean()
        std_20 = data['Close'].rolling(window=20).std()
        upper_band = sma_20 + (std_20 * 2)
        lower_band = sma_20 - (std_20 * 2)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#1A73E8', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=data.index,
            y=upper_band,
            mode='lines',
            name='Upper BB',
            line=dict(color='#28A745', width=1.5, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=data.index,
            y=lower_band,
            mode='lines',
            name='Lower BB',
            line=dict(color='#DC3545', width=1.5, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=data.index,
            y=sma_20,
            mode='lines',
            name='20-Day SMA',
            line=dict(color='#FFC107', width=1.5)
        ))
        bg_color = "#16213e" if st.session_state.dark_mode else "white"
        text_color = "#e0e0e0" if st.session_state.dark_mode else "#1a1a2e"
        grid_color = "#2a2a4e" if st.session_state.dark_mode else "#f0f0f0"
        fig.update_layout(
            title='Bollinger Bands (20-day, 2 Std Dev)',
            height=300,
            template="plotly_white" if not st.session_state.dark_mode else "plotly_dark",
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color,
            font_color=text_color
        )
        fig.update_xaxes(showgrid=True, gridcolor=grid_color)
        fig.update_yaxes(showgrid=True, gridcolor=grid_color)
        return fig
    except:
        return None

def format_number(value):
    if value is None or value == 'N/A':
        return 'N/A'
    try:
        if abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:.2f}"
    except:
        return 'N/A'

def format_percent(value):
    if value is None or value == 'N/A':
        return 'N/A'
    try:
        return f"{value*100:.2f}%"
    except:
        return 'N/A'

def generate_pdf_report(ticker):
    """Generate a simple PDF report for a stock"""
    try:
        hist, info = get_stock_data(ticker)
        if hist is None or hist.empty:
            return None
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, f"Stock Report: {ticker}", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(100, 8, "Metric", 1)
        pdf.cell(90, 8, "Value", 1)
        pdf.ln()
        
        pdf.set_font("Arial", "", 10)
        current = float(hist['Close'].iloc[-1])
        first = float(hist['Close'].iloc[0])
        change = ((current / first) - 1) * 100
        
        metrics = [
            ("Current Price", f"${current:.2f}"),
            ("1-Year Change", f"{change:+.1f}%"),
            ("P/E Ratio", str(info.get('trailingPE', 'N/A'))),
            ("EPS (TTM)", f"${info.get('trailingEps', 'N/A')}" if info.get('trailingEps') else 'N/A'),
            ("Market Cap", format_number(info.get('marketCap', 'N/A'))),
            ("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else 'N/A'),
            ("Beta", str(info.get('beta', 'N/A'))),
        ]
        
        for label, value in metrics:
            pdf.cell(100, 8, label, 1)
            pdf.cell(90, 8, str(value), 1)
            pdf.ln()
        
        # Add footer
        pdf.ln(10)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(200, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        pdf.cell(200, 6, "Data provided by Yahoo Finance", ln=True, align='C')
        
        return pdf.output(dest='S').encode('latin-1')
    except:
        return None

# --- WATCHLIST FUNCTIONS ---
def add_to_watchlist(ticker):
    ticker = ticker.upper()
    if ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(ticker)
        return True
    return False

def remove_from_watchlist(ticker):
    ticker = ticker.upper()
    if ticker in st.session_state.watchlist:
        st.session_state.watchlist.remove(ticker)
        return True
    return False

# --- OVERVIEW PAGE ---
def show_overview():
    st.markdown(get_css(), unsafe_allow_html=True)
    
    # --- HEADER ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🌙" if not st.session_state.dark_mode else "☀️", help="Toggle Dark Mode"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    with col2:
        st.markdown("""
            <div style="background-color:#ADD8E6;padding:20px;border-radius:10px;text-align:center;margin-bottom:20px;">
                <h1 style="color:#000000;margin:0;font-size:36px;">Market Analysis Dashboard</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.write("")  # Spacer
    
    # --- SEARCH + WATCHLIST ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p style="text-align:center;color:#6c757d;font-size:14px;">Search for a stock to analyze</p>', unsafe_allow_html=True)
        selected_stock = st.selectbox(
            "Select a stock",
            options=sorted(ALL_STOCKS),
            index=sorted(ALL_STOCKS).index("AAPL") if "AAPL" in ALL_STOCKS else 0,
            label_visibility="collapsed"
        )
        
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 1, 1, 1])
        with col_btn2:
            if st.button("🔍 Analyze", use_container_width=True):
                st.session_state.selected_ticker = selected_stock
                st.session_state.page = 'analysis'
                st.rerun()
        with col_btn3:
            if st.button("⭐ Add to Watchlist", use_container_width=True):
                if add_to_watchlist(selected_stock):
                    st.success(f"Added {selected_stock} to watchlist!")
                else:
                    st.info(f"{selected_stock} already in watchlist")
    
    # --- WATCHLIST DISPLAY ---
    if st.session_state.watchlist:
        st.subheader("📋 Watchlist")
        watchlist_cols = st.columns(min(5, len(st.session_state.watchlist)))
        for i, ticker in enumerate(st.session_state.watchlist[:10]):
            with watchlist_cols[i % 5]:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    if st.button(ticker, key=f"wl_{ticker}", use_container_width=True):
                        st.session_state.selected_ticker = ticker
                        st.session_state.page = 'analysis'
                        st.rerun()
                with col_b:
                    if st.button("✕", key=f"del_{ticker}", help="Remove from watchlist"):
                        remove_from_watchlist(ticker)
                        st.rerun()
    
    st.markdown("---")
    
    # --- MARKET INDICES ROW ---
    st.subheader("Market Indices")
    indices_data = get_indices()
    cols = st.columns(4)
    
    for i, (name, data) in enumerate(indices_data.items()):
        with cols[i]:
            if data is not None and not data.empty:
                try:
                    fig = create_candlestick_chart(data, name, 250)
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                        
                        current = float(data['Close'].iloc[-1])
                        prev = float(data['Close'].iloc[0])
                        change = ((current - prev) / prev) * 100
                        if change >= 0:
                            st.write(f"**${current:.2f}** 🟢 {change:+.2f}%")
                        else:
                            st.write(f"**${current:.2f}** 🔴 {change:+.2f}%")
                    else:
                        st.write(f"**{name}** - Chart unavailable")
                except Exception as e:
                    st.write(f"**{name}** - Error loading data")
            else:
                st.write(f"**{name}** - No data available")
    
    st.markdown("---")
    
    # --- MARKET ANALYSIS ROW: VIX + Bollinger Bands ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("VIX (Volatility Index)")
        vix_data = get_vix_data()
        if vix_data is not None and not vix_data.empty:
            fig = create_vix_chart(vix_data)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
                current = float(vix_data['Close'].iloc[-1])
                prev = float(vix_data['Close'].iloc[0])
                change = ((current - prev) / prev) * 100
                change_color = "🟢" if change < 0 else "🔴"
                st.write(f"**Current VIX: {current:.2f}** {change_color} {change:+.2f}%")
            else:
                st.info("VIX data unavailable")
        else:
            st.info("VIX data unavailable")
    
    with col_right:
        st.subheader("Bollinger Bands (20-day, 2 Std Dev)")
        spy_data = get_sp500_data()
        if spy_data is not None and not spy_data.empty:
            fig = create_bollinger_bands_chart(spy_data)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Bollinger Bands data unavailable")
        else:
            st.info("Bollinger Bands data unavailable")
    
    st.markdown("---")
    
    # --- S&P 500 125-day Moving Average ---
    st.subheader("S&P 500 and its 125-day Moving Average")
    spy_data = get_sp500_data()
    if spy_data is not None and not spy_data.empty:
        fig = create_sp500_ma_chart(spy_data)
        if fig is not None:
            current_price = spy_data['Close'].iloc[-1]
            ma_125 = spy_data['Close'].rolling(window=125).mean().iloc[-1]
            if not pd.isna(ma_125):
                position = "Above" if current_price > ma_125 else "Below"
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current S&P 500", f"${current_price:.2f}")
                with col2:
                    st.metric("125-Day MA", f"${ma_125:.2f}")
                with col3:
                    st.metric("Position", position, delta=f"{((current_price - ma_125) / ma_125 * 100):+.2f}%")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("S&P 500 data unavailable")
    else:
        st.info("S&P 500 data unavailable")
    
    st.markdown("---")
    
    # --- HEAT MAP: Daily Performers ---
    st.subheader("Daily Performers")
    
    heatmap_data = []
    for ticker in HEATMAP_STOCKS:
        change = get_daily_change(ticker)
        heatmap_data.append({'Ticker': ticker, 'Change': change})
    
    cols = st.columns(5)
    for i, stock in enumerate(heatmap_data):
        with cols[i % 5]:
            if stock['Change'] > 0:
                color = "#28a745"
            elif stock['Change'] < 0:
                color = "#dc3545"
            else:
                color = "#6c757d"
            
            sign = '+' if stock['Change'] >= 0 else ''
            button_label = f"{stock['Ticker']}\n{sign}{stock['Change']:.1f}%"
            
            bg_color = "#16213e" if st.session_state.dark_mode else "white"
            st.markdown(f"""
                <style>
                    div[data-testid="column"]:nth-child({i % 5 + 1}) div.stButton > button {{
                        background-color: {color} !important;
                        color: white !important;
                        font-weight: 700;
                        font-size: 16px;
                        padding: 25px 10px;
                        border-radius: 8px;
                        border: none;
                        width: 100%;
                        white-space: pre-line;
                        line-height: 1.6;
                        margin: 4px 0;
                        height: auto;
                        min-height: 70px;
                        cursor: pointer;
                    }}
                    div[data-testid="column"]:nth-child({i % 5 + 1}) div.stButton > button:hover {{
                        opacity: 0.8;
                        transform: scale(1.02);
                        transition: all 0.2s;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    }}
                </style>
            """, unsafe_allow_html=True)
            
            if st.button(button_label, key=f"hm_{stock['Ticker']}", use_container_width=True):
                st.session_state.selected_ticker = stock['Ticker']
                st.session_state.page = 'analysis'
                st.rerun()
    
    st.markdown("---")
    
    # --- NEWS SECTION ---
    st.subheader("Market News")
    
    news_items = get_yahoo_news()
    
    if news_items:
        for i, news in enumerate(news_items[:8]):
            with st.container():
                text_color = "#e0e0e0" if st.session_state.dark_mode else "#1a1a2e"
                bg_news = "#16213e" if st.session_state.dark_mode else "#f8f9fa"
                st.markdown(f"""
                    <div style="background-color:{bg_news};padding:12px 15px;border-radius:8px;border-left:4px solid #ADD8E6;margin-bottom:8px;">
                        <a href="{news['link']}" target="_blank" style="text-decoration:none;color:{text_color};font-weight:500;font-size:14px;">
                            {news['title']}
                        </a>
                        <div style="font-size:12px;color:#6c757d;">Source: {news['publisher']}</div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No news available at this time")
    
    st.markdown("---")
    st.markdown(f"""
        <div class="footer">
            Built by Deborah Harmon | Data provided by Yahoo Finance | {len(ALL_STOCKS)} stocks available
            <br>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    """, unsafe_allow_html=True)

# --- ANALYSIS PAGE ---
def show_analysis(ticker):
    st.markdown(get_css(), unsafe_allow_html=True)
    
    # --- HEADER ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🌙" if not st.session_state.dark_mode else "☀️", help="Toggle Dark Mode"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    with col2:
        st.markdown(f"""
            <div style="background-color:#ADD8E6;padding:15px;border-radius:10px;text-align:center;margin-bottom:20px;">
                <h1 style="color:#000000;margin:0;font-size:28px;">{ticker} Stock Analysis</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("📄 Export PDF", help="Download PDF report"):
            pdf_data = generate_pdf_report(ticker)
            if pdf_data:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_data,
                    file_name=f"{ticker}_report.pdf",
                    mime="application/pdf"
                )
    
    # --- BACK + WATCHLIST BUTTONS ---
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("← Back to Market Overview"):
            st.session_state.page = 'overview'
            st.session_state.selected_ticker = None
            st.rerun()
    with col2:
        if ticker in st.session_state.watchlist:
            if st.button("⭐ Remove from Watchlist", use_container_width=True):
                remove_from_watchlist(ticker)
                st.rerun()
        else:
            if st.button("⭐ Add to Watchlist", use_container_width=True):
                add_to_watchlist(ticker)
                st.rerun()
    
    time_options = {
        "1 Year": ("1y", "1d"),
        "6 Months": ("6mo", "1d"),
        "3 Months": ("3mo", "1d"),
        "1 Month": ("1mo", "1d"),
        "5 Days": ("5d", "5m"),
        "4 Hours": ("5d", "1h"),
        "1 Hour": ("1d", "5m"),
        "30 Minutes": ("1d", "1m"),
        "5 Minutes": ("1d", "1m"),
        "1 Minute": ("1d", "1m"),
    }
    
    selected_period = st.selectbox("Select Time Period", list(time_options.keys()), index=0)
    period, interval = time_options[selected_period]
    
    hist, info = get_stock_data(ticker, period=period, interval=interval)
    
    if hist is None or hist.empty:
        st.error(f"No data found for {ticker}")
        st.info("💡 Try a different stock like: **AAPL**, **MSFT**, **GOOGL**, **AMZN**, or **NVDA**")
        return
    
    fig = create_candlestick_chart(hist, f"{ticker} Price Chart ({selected_period})", 500)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Not enough data for this time period. Try a longer period.")
        return
    
    current = float(hist['Close'].iloc[-1])
    first = float(hist['Close'].iloc[0])
    change = ((current / first) - 1) * 100
    
    text_color = "#e0e0e0" if st.session_state.dark_mode else "#1a1a2e"
    bg_color = "#16213e" if st.session_state.dark_mode else "#f8f9fa"
    border_color = "#2a2a4e" if st.session_state.dark_mode else "#e9ecef"
    
    st.markdown(f"""
        <div style="background-color:{bg_color};padding:15px;border-radius:10px;border:1px solid {border_color};margin-bottom:20px;">
            <div style="display:flex;justify-content:space-around;text-align:center;">
                <div>
                    <div style="color:#6c757d;font-size:12px;text-transform:uppercase;">Current Price</div>
                    <div style="font-size:24px;font-weight:700;color:{text_color};">${current:.2f}</div>
                </div>
                <div>
                    <div style="color:#6c757d;font-size:12px;text-transform:uppercase;">Change</div>
                    <div style="font-size:24px;font-weight:700;color:{'#28a745' if change >= 0 else '#dc3545'};">{change:+.1f}%</div>
                </div>
                <div>
                    <div style="color:#6c757d;font-size:12px;text-transform:uppercase;">Volume</div>
                    <div style="font-size:24px;font-weight:700;color:{text_color};">{int(hist['Volume'].iloc[-1]):,}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Comprehensive Stock Analysis")
    
    valuation_data = {
        "Metric": [
            "Market Cap", "Enterprise Value", "P/E Ratio", "Forward P/E", "PEG Ratio",
            "P/S Ratio", "P/B Ratio"
        ],
        "Value": [
            format_number(info.get('marketCap', 'N/A')),
            format_number(info.get('enterpriseValue', 'N/A')),
            info.get('trailingPE', 'N/A'),
            info.get('forwardPE', 'N/A'),
            info.get('pegRatio', 'N/A'),
            info.get('priceToSalesTrailing12Months', 'N/A'),
            info.get('priceToBook', 'N/A'),
        ]
    }
    
    performance_data = {
        "Metric": [
            "EPS (TTM)", "EPS Growth", "Revenue Growth", "Profit Margin", "ROE", "ROA"
        ],
        "Value": [
            f"${info.get('trailingEps', 'N/A')}" if info.get('trailingEps') else 'N/A',
            format_percent(info.get('earningsGrowth', 'N/A')),
            format_percent(info.get('revenueGrowth', 'N/A')),
            format_percent(info.get('profitMargins', 'N/A')),
            format_percent(info.get('returnOnEquity', 'N/A')),
            format_percent(info.get('returnOnAssets', 'N/A')),
        ]
    }
    
    health_data = {
        "Metric": [
            "Current Ratio", "Quick Ratio", "Debt/Equity", "Gross Margin", 
            "Operating Margin", "Dividend Yield", "Payout Ratio"
        ],
        "Value": [
            info.get('currentRatio', 'N/A'),
            info.get('quickRatio', 'N/A'),
            info.get('debtToEquity', 'N/A'),
            format_percent(info.get('grossMargins', 'N/A')),
            format_percent(info.get('operatingMargins', 'N/A')),
            format_percent(info.get('dividendYield', 'N/A')),
            format_percent(info.get('payoutRatio', 'N/A')),
        ]
    }
    
    stats_data = {
        "Metric": [
            "Beta", "52-Week High", "52-Week Low", "Short Ratio", "Avg Volume"
        ],
        "Value": [
            info.get('beta', 'N/A'),
            f"${info.get('fiftyTwoWeekHigh', 'N/A')}" if info.get('fiftyTwoWeekHigh') else 'N/A',
            f"${info.get('fiftyTwoWeekLow', 'N/A')}" if info.get('fiftyTwoWeekLow') else 'N/A',
            info.get('shortRatio', 'N/A'),
            f"{info.get('averageVolume', 0):,}" if info.get('averageVolume') else 'N/A',
        ]
    }
    
    tab1, tab2, tab3, tab4 = st.tabs(["Valuation", "Performance", "Financial Health", "Statistics"])
    
    with tab1:
        df_val = pd.DataFrame(valuation_data)
        st.dataframe(df_val, use_container_width=True, hide_index=True)
    
    with tab2:
        df_perf = pd.DataFrame(performance_data)
        st.dataframe(df_perf, use_container_width=True, hide_index=True)
    
    with tab3:
        df_health = pd.DataFrame(health_data)
        st.dataframe(df_health, use_container_width=True, hide_index=True)
    
    with tab4:
        df_stats = pd.DataFrame(stats_data)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
    
    st.subheader("Additional Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**Income**")
        st.write(f"Income: {format_number(info.get('netIncomeToCommon', 'N/A'))}")
        st.write(f"Sales: {format_number(info.get('totalRevenue', 'N/A'))}")
        st.write(f"Book/sh: ${info.get('bookValue', 'N/A')}")
        st.write(f"Cash/sh: ${info.get('cashPerShare', 'N/A')}")
    
    with col2:
        st.markdown("**Employees & IPO**")
        st.write(f"Employees: {info.get('fullTimeEmployees', 'N/A')}")
        st.write(f"Sector: {info.get('sector', 'N/A')}")
        st.write(f"Industry: {info.get('industry', 'N/A')}")
    
    with col3:
        st.markdown("**Performance**")
        perf_year = f"{info.get('52WeekChange', 0)*100:.2f}%" if info.get('52WeekChange') else 'N/A'
        st.write(f"Perf Year: {perf_year}")
        st.write(f"Beta: {info.get('beta', 'N/A')}")
    
    with col4:
        st.markdown("**Analyst**")
        st.write(f"Recommendation: {info.get('recommendationKey', 'N/A')}")
        st.write(f"Target Price: ${info.get('targetMeanPrice', 'N/A')}")
        st.write(f"Analysts: {info.get('numberOfAnalystOpinions', 'N/A')}")
    
    st.markdown("---")
    st.markdown(f"""
        <div class="footer">
            Built by [Your Name] | Data provided by Yahoo Finance
            <br>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    """, unsafe_allow_html=True)

# --- MAIN ---
if st.session_state.page == 'overview':
    show_overview()
elif st.session_state.page == 'analysis' and st.session_state.selected_ticker:
    show_analysis(st.session_state.selected_ticker)
else:
    st.session_state.page = 'overview'
    st.rerun()
