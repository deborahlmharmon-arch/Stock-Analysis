import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta

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

# --- TOP 10 S&P 500 STOCKS FOR HEAT MAP ---
HEATMAP_STOCKS = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'GOOGL', 'TSLA', 'JPM', 'VZ', 'KO']

# --- ALL STOCKS ---
ALL_STOCKS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "JPM", "VZ", "KO",
    "GOOG", "NFLX", "ADBE", "PEP", "COST", "AVGO", "TXN", "QCOM", "AMGN", "INTU"
]

# --- CUSTOM CSS ---
def get_css():
    if st.session_state.dark_mode:
        return """
            <style>
                .stApp { background-color: #1a1a2e; color: #e0e0e0; }
                .main-header { background-color: #16213e; border-bottom: 2px solid #0f3460; }
                .metric-card { background-color: #16213e; border: 1px solid #2a2a4e; }
            </style>
        """
    else:
        return """
            <style>
                .stApp { background-color: #FFFFFF; }
                .main-header { background-color: #f8f9fa; border-bottom: 1px solid #e9ecef; }
                .metric-card { background-color: #f8f9fa; border: 1px solid #e9ecef; }
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
            data = yf.download(symbol, period="5d", interval="1d")
            if data is not None and not data.empty and len(data) >= 2:
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

def get_yahoo_news():
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/search?q=stock%20market"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            news_items = []
            if 'news' in data:
                for item in data['news'][:8]:
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
        fig.update_layout(
            title=title,
            height=height,
            template="plotly_white",
            showlegend=False,
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        fig.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
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
        fig.update_layout(
            title='VIX (Volatility Index)',
            height=300,
            template="plotly_white",
            hovermode='x unified',
            margin=dict(l=10, r=10, t=40, b=10)
        )
        fig.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
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
        fig.update_layout(
            title='S&P 500 vs 125-Day Moving Average',
            height=300,
            template="plotly_white",
            hovermode='x unified',
            margin=dict(l=10, r=10, t=40, b=10)
        )
        fig.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
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
        fig.update_layout(
            title='Bollinger Bands (20-day, 2 Std Dev)',
            height=300,
            template="plotly_white",
            hovermode='x unified',
            margin=dict(l=10, r=10, t=40, b=10)
        )
        fig.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
        return fig
    except:
        return None

# --- OVERVIEW PAGE ---
def show_overview():
    st.markdown(get_css(), unsafe_allow_html=True)
    
    # Title
    st.markdown("""
        <div style="background-color:#ADD8E6;padding:20px;border-radius:10px;text-align:center;margin-bottom:20px;">
            <h1 style="color:#000000;margin:0;font-size:36px;">Market Analysis Dashboard</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Search
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p style="text-align:center;color:#6c757d;font-size:14px;">Search for a stock to analyze</p>', unsafe_allow_html=True)
        selected_stock = st.selectbox(
            "Select a stock",
            options=sorted(ALL_STOCKS),
            index=0,
            label_visibility="collapsed"
        )
        if st.button("🔍 Analyze Stock", use_container_width=True):
            st.session_state.selected_ticker = selected_stock
            st.session_state.page = 'analysis'
            st.rerun()
    
    st.markdown("---")
    
    # --- MARKET INDICES ---
    st.subheader("Market Indices")
    indices_data = get_indices()
    cols = st.columns(4)
    
    if indices_data:
        for i, (name, data) in enumerate(indices_data.items()):
            with cols[i]:
                if data is not None and not data.empty and len(data) >= 2:
                    fig = create_candlestick_chart(data, name, 250)
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                        current = float(data['Close'].iloc[-1])
                        prev = float(data['Close'].iloc[-2])
                        change = ((current - prev) / prev) * 100
                        if change >= 0:
                            st.write(f"**${current:.2f}** 🟢 {change:+.2f}%")
                        else:
                            st.write(f"**${current:.2f}** 🔴 {change:+.2f}%")
                    else:
                        st.write(f"**{name}** - Chart unavailable")
                else:
                    st.write(f"**{name}** - No data available")
    else:
        st.warning("Market indices data temporarily unavailable.")
    
    st.markdown("---")
    
    # --- VIX + BOLLINGER BANDS ---
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
    
    with col_right:
        st.subheader("Bollinger Bands (20-day, 2 Std Dev)")
        spy_data = get_sp500_data()
        if spy_data is not None and not spy_data.empty:
            fig = create_bollinger_bands_chart(spy_data)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Bollinger Bands data unavailable")
    
    st.markdown("---")
    
    # --- S&P 500 125-DAY MA ---
    st.subheader("S&P 500 and its 125-day Moving Average")
    spy_data = get_sp500_data()
    if spy_data is not None and not spy_data.empty:
        fig = create_sp500_ma_chart(spy_data)
        if fig is not None:
            current_price = spy_data['Close'].iloc[-1]
            ma_125 = spy_data['Close'].rolling(window=125).mean().iloc[-1]
            if not pd.isna(ma_125):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current S&P 500", f"${current_price:.2f}")
                with col2:
                    st.metric("125-Day MA", f"${ma_125:.2f}")
                with col3:
                    position = "Above" if current_price > ma_125 else "Below"
                    st.metric("Position", position, delta=f"{((current_price - ma_125) / ma_125 * 100):+.2f}%")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chart unavailable")
    else:
        st.info("S&P 500 data unavailable")
    
    st.markdown("---")
    
    # --- HEAT MAP ---
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
                </style>
            """, unsafe_allow_html=True)
            
            if st.button(button_label, key=f"hm_{stock['Ticker']}", use_container_width=True):
                st.session_state.selected_ticker = stock['Ticker']
                st.session_state.page = 'analysis'
                st.rerun()
    
    st.markdown("---")
    
    # --- NEWS ---
    st.subheader("Market News")
    news_items = get_yahoo_news()
    if news_items:
        for news in news_items:
            with st.container():
                bg_color = "#16213e" if st.session_state.dark_mode else "#f8f9fa"
                st.markdown(f"""
                    <div style="background-color:{bg_color};padding:12px 15px;border-radius:8px;border-left:4px solid #ADD8E6;margin-bottom:8px;">
                        <a href="{news['link']}" target="_blank" style="text-decoration:none;color:#1a1a2e;font-weight:500;font-size:14px;">
                            {news['title']}
                        </a>
                        <div style="font-size:12px;color:#6c757d;">Source: {news['publisher']}</div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No news available")
    
    st.markdown("---")
    st.caption(f"Built by [Your Name] | Data provided by Yahoo Finance | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# --- ANALYSIS PAGE ---
def show_analysis(ticker):
    if st.button("← Back to Market Overview"):
        st.session_state.page = 'overview'
        st.session_state.selected_ticker = None
        st.rerun()
    
    st.markdown(f"""
        <div style="background-color:#ADD8E6;padding:15px;border-radius:10px;text-align:center;margin-bottom:20px;">
            <h1 style="color:#000000;margin:0;font-size:28px;">{ticker} Stock Analysis</h1>
        </div>
    """, unsafe_allow_html=True)
    
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
        return
    
    fig = create_candlestick_chart(hist, f"{ticker} Price Chart ({selected_period})", 500)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Not enough data for this time period.")
        return
    
    current = float(hist['Close'].iloc[-1])
    first = float(hist['Close'].iloc[0])
    change = ((current / first) - 1) * 100
    
    st.markdown(f"""
        <div style="background-color:#f8f9fa;padding:15px;border-radius:10px;border:1px solid #e9ecef;margin-bottom:20px;">
            <div style="display:flex;justify-content:space-around;text-align:center;">
                <div>
                    <div style="color:#6c757d;font-size:12px;text-transform:uppercase;">Current Price</div>
                    <div style="font-size:24px;font-weight:700;">${current:.2f}</div>
                </div>
                <div>
                    <div style="color:#6c757d;font-size:12px;text-transform:uppercase;">Change</div>
                    <div style="font-size:24px;font-weight:700;color:{'#28a745' if change >= 0 else '#dc3545'};">{change:+.1f}%</div>
                </div>
                <div>
                    <div style="color:#6c757d;font-size:12px;text-transform:uppercase;">Volume</div>
                    <div style="font-size:24px;font-weight:700;">{int(hist['Volume'].iloc[-1]):,}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Quick Metrics
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("P/E", info.get('trailingPE', 'N/A'))
    with col2:
        eps = info.get('trailingEps', 'N/A')
        st.metric("EPS", f"${eps:.2f}" if eps != 'N/A' else "N/A")
    with col3:
        st.metric("Market Cap", format_number(info.get('marketCap', 'N/A')))
    with col4:
        div = info.get('dividendYield', 0)
        st.metric("Dividend", f"{div*100:.2f}%" if div else "N/A")

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

# --- MAIN ---
if st.session_state.page == 'overview':
    show_overview()
elif st.session_state.page == 'analysis' and st.session_state.selected_ticker:
    show_analysis(st.session_state.selected_ticker)
else:
    st.session_state.page = 'overview'
    st.rerun()
