import streamlit as st
import sys
from pathlib import Path

# Simple page routing without complex imports
def main():
    st.set_page_config(
        page_title="AI Trading Analyzer",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🤖 AI Trading Analyzer")
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose Analysis Type",
        ["Home", "Stocks", "Options", "Futures"]
    )
    
    # Route to appropriate page
    if page == "Home":
        home_page()
    elif page == "Stocks":
        stocks_page()
    elif page == "Options":
        options_page()
    elif page == "Futures":
        futures_page()

def home_page():
    st.header("Welcome to AI Trading Analyzer")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📈 Stocks")
        st.write("Analyze stocks with technical indicators and AI predictions")
        
    with col2:
        st.subheader("⚡ Options")
        st.write("View options chains and analyze volatility")
        
    with col3:
        st.subheader("🚀 Futures")
        st.write("Trade futures with advanced analytics")
    
    st.markdown("---")
    st.info("👈 Use the sidebar to navigate to different analysis tools")

def stocks_page():
    import yfinance as yf
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np
    
    st.header("📈 Stock Analysis")
    
    # Sidebar controls
    st.sidebar.subheader("Stock Selection")
    symbol = st.sidebar.text_input("Enter Symbol", value="AAPL").upper()
    period = st.sidebar.selectbox("Time Period", ["1d", "5d", "1mo", "3mo", "1y"], index=2)
    
    if st.sidebar.button("Analyze Stock", type="primary"):
        try:
            with st.spinner(f"Fetching data for {symbol}..."):
                # Fetch stock data
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period)
                info = ticker.info
            
            if not data.empty:
                # Display basic info
                st.subheader(f"{symbol} - {info.get('longName', symbol)}")
                
                # Metrics
                latest_price = data['Close'].iloc[-1]
                change = data['Close'].iloc[-1] - data['Close'].iloc[-2]
                change_pct = (change / data['Close'].iloc[-2]) * 100
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Price", f"${latest_price:.2f}", f"{change:.2f} ({change_pct:.1f}%)")
                with col2:
                    st.metric("Volume", f"{data['Volume'].iloc[-1]:,.0f}")
                with col3:
                    st.metric("Market Cap", info.get('marketCap', 'N/A'))
                
                # Price chart
                fig = go.Figure(data=go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name="Price"
                ))
                
                # Add moving averages
                data['SMA_20'] = data['Close'].rolling(window=20).mean()
                data['SMA_50'] = data['Close'].rolling(window=50).mean()
                
                fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name='SMA 20', line=dict(color='blue')))
                fig.add_trace(go.Scatter(x=data.index, y=data['SMA_50'], name='SMA 50', line=dict(color='orange')))
                
                fig.update_layout(
                    title=f"{symbol} Price Chart",
                    yaxis_title="Price ($)",
                    xaxis_title="Date",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Simple RSI calculation
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Technical Indicators")
                    current_rsi = rsi.iloc[-1]
                    st.metric("RSI (14)", f"{current_rsi:.1f}")
                    
                    if current_rsi > 70:
                        st.error("🔴 Overbought Signal")
                    elif current_rsi < 30:
                        st.success("🟢 Oversold Signal")
                    else:
                        st.info("🟡 Neutral")
                
                with col2:
                    st.subheader("Moving Average Signal")
                    current_price = data['Close'].iloc[-1]
                    sma_20 = data['SMA_20'].iloc[-1]
                    sma_50 = data['SMA_50'].iloc[-1]
                    
                    if current_price > sma_20 > sma_50:
                        st.success("🟢 Strong Bullish Trend")
                    elif current_price > sma_20:
                        st.info("🟡 Bullish")
                    elif current_price < sma_20 < sma_50:
                        st.error("🔴 Strong Bearish Trend")
                    else:
                        st.warning("🟡 Bearish")
            
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")

def options_page():
    import yfinance as yf
    import pandas as pd
    
    st.header("⚡ Options Analysis")
    
    st.sidebar.subheader("Options Selection")
    symbol = st.sidebar.text_input("Enter Symbol", value="AAPL").upper()
    
    if st.sidebar.button("Load Options", type="primary"):
        try:
            with st.spinner(f"Loading options for {symbol}..."):
                ticker = yf.Ticker(symbol)
                expirations = ticker.options
                
                if expirations:
                    expiration = st.selectbox("Select Expiration", expirations)
                    
                    opt = ticker.option_chain(expiration)
                    calls = opt.calls
                    puts = opt.puts
                    
                    # Get current price
                    current_price = ticker.history(period="1d")['Close'].iloc[-1]
                    
                    st.subheader(f"{symbol} Options Chain - {expiration}")
                    st.info(f"Current Stock Price: ${current_price:.2f}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📞 Calls")
                        calls_display = calls[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'impliedVolatility']].head(10)
                        st.dataframe(calls_display)
                        
                        # Simple analytics
                        total_call_volume = calls['volume'].sum()
                        st.metric("Total Call Volume", f"{total_call_volume:,}")
                    
                    with col2:
                        st.subheader("📉 Puts")
                        puts_display = puts[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'impliedVolatility']].head(10)
                        st.dataframe(puts_display)
                        
                        total_put_volume = puts['volume'].sum()
                        st.metric("Total Put Volume", f"{total_put_volume:,}")
                    
                    # Put/Call ratio
                    put_call_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else 0
                    st.metric("Put/Call Ratio", f"{put_call_ratio:.2f}")
                    
                else:
                    st.warning(f"No options data available for {symbol}")
                    
        except Exception as e:
            st.error(f"Error loading options: {str(e)}")

def futures_page():
    import yfinance as yf
    import plotly.graph_objects as go
    
    st.header("🚀 Futures Analysis")
    
    # Common futures contracts
    futures_symbols = {
        "ES=F": "S&P 500 E-mini",
        "NQ=F": "NASDAQ 100 E-mini",
        "YM=F": "Dow Jones E-mini",
        "CL=F": "Crude Oil",
        "GC=F": "Gold",
        "SI=F": "Silver"
    }
    
    st.sidebar.subheader("Futures Selection")
    selected = st.sidebar.selectbox(
        "Choose Contract",
        options=list(futures_symbols.keys()),
        format_func=lambda x: f"{x} - {futures_symbols[x]}"
    )
    
    period = st.sidebar.selectbox("Period", ["1d", "5d", "1mo", "3mo"], index=1)
    
    if st.sidebar.button("Analyze Futures", type="primary"):
        try:
            with st.spinner(f"Loading {futures_symbols[selected]}..."):
                ticker = yf.Ticker(selected)
                data = ticker.history(period=period)
            
            if not data.empty:
                st.subheader(f"{futures_symbols[selected]} ({selected})")
                
                # Basic metrics
                latest_price = data['Close'].iloc[-1]
                change = data['Close'].iloc[-1] - data['Close'].iloc[-2]
                change_pct = (change / data['Close'].iloc[-2]) * 100
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Current Price", f"${latest_price:.2f}", f"{change:.2f} ({change_pct:.1f}%)")
                with col2:
                    st.metric("Volume", f"{data['Volume'].iloc[-1]:,.0f}")
                
                # Chart
                fig = go.Figure(data=go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close']
                ))
                
                fig.update_layout(
                    title=f"{selected} Futures Chart",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error loading futures data: {str(e)}")

if __name__ == "__main__":
    main()
