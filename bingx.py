import time
import requests
import pandas as pd
import ta  # Technical Analysis library

# ✅ BingX API URLs
BINGX_BASE_URL = "https://api.bingx.com/api/v1/market"
BINGX_GAINERS_URL = "https://api.bingx.com/api/v1/market/tickers"

# ✅ AI API Key (Replace with your actual API key)
AI_API_KEY = "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"

# ✅ Supported Trading Modes
TRADING_MODES = {"1": "spot", "2": "futures"}

# ✅ Fetch Crypto Market Data from BingX (Spot & Futures)
def get_crypto_data(symbol="BTC-USDT", interval="1h", limit=50, mode="spot"):
    url = f"{BINGX_BASE_URL}"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "type": mode  # "spot" or "futures"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "data" not in data:
            print(f"⚠️ BingX API Error: {data}")
            return pd.DataFrame()

        df = pd.DataFrame(data["data"], columns=["time", "open", "high", "low", "close", "volume"])
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print(f"⚠️ BingX API Request Failed: {e}")
        return pd.DataFrame()

# ✅ Fetch Top Gainers from BingX
def get_top_gainers():
    try:
        response = requests.get(BINGX_GAINERS_URL)
        data = response.json()
        
        if "data" not in data:
            print(f"⚠️ BingX Gainers API Error: {data}")
            return {}

        # Sort by percentage change and get the top 5 gainers
        gainers = sorted(data["data"], key=lambda x: float(x["changeRate"]), reverse=True)[:5]
        
        return {str(i + 3): g["symbol"] for i, g in enumerate(gainers)}
    except Exception as e:
        print(f"⚠️ Failed to fetch top gainers: {e}")
        return {}

# ✅ Perform Market Analysis using Technical Indicators
def analyze_market(df):
    if df.empty:
        print("⚠️ No market data available. Skipping analysis...")
        return None

    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["macd"] = ta.trend.MACD(df["close"]).macd()
    df["ema_50"] = ta.trend.EMAIndicator(df["close"], window=50).ema_indicator()
    df["bollinger_high"] = ta.volatility.BollingerBands(df["close"]).bollinger_hband()
    df["bollinger_low"] = ta.volatility.BollingerBands(df["close"]).bollinger_lband()

    return df.iloc[-1]  # Get latest market data

# ✅ AI-Powered Trading Signal
def get_ai_trading_signal(market_data, asset):
    if market_data is None:
        return "⚠️ No market data available for AI analysis."

    prompt = f"""
    Given the following market conditions for {asset}:
    - RSI: {market_data['rsi']}
    - MACD: {market_data['macd']}
    - EMA-50: {market_data['ema_50']}
    - Bollinger Bands: High {market_data['bollinger_high']}, Low {market_data['bollinger_low']}
    
    Predict the best trade signal (Buy, Sell, Hold) with Entry, Stop Loss, and Take Profit in JSON format like this:
    
      "signal": "",
      "entry": "",
      "stop_loss": "",    
      "take_profit": "",  
      "asset": "" 
    """

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "google/gemma-3-1b-it:free",
        "messages": [
            {"role": "system", "content": "You are an expert financial trading assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"]
        else:
            return f"⚠️ AI Error: {result}"
    except Exception as e:
        return f"⚠️ AI Request Failed: {e}"

# ✅ User Selection & Execution
def main():
    print("\n📌 Select Trading Mode:")
    for key, value in TRADING_MODES.items():
        print(f"{key} - {value.capitalize()}")

    mode_choice = input("\nEnter the option number: ")
    mode = TRADING_MODES.get(mode_choice)

    if not mode:
        print("⚠️ Invalid selection. Exiting.")
        return

    # Fetch top gainers and add them to trading pairs
    top_gainers = get_top_gainers()
    
    TRADING_PAIRS = {
        "1": "BTC-USDT",
        "2": "ETH-USDT",
        **top_gainers
    }

    print("\n📌 Select a Trading Pair:")
    for key, value in TRADING_PAIRS.items():
        print(f"{key} - {value}")

    choice = input("\nEnter the option number: ")
    asset = TRADING_PAIRS.get(choice)

    if not asset:
        print("⚠️ Invalid selection. Exiting.")
        return

    print(f"\n📊 Fetching real-time data for {asset} ({mode})...")

    while True:
        try:
            market_data = get_crypto_data(asset, mode=mode)
            if market_data.empty:
                time.sleep(10)
                continue  # Skip this loop if no data

            latest_market = analyze_market(market_data)
            if latest_market is None:
                time.sleep(10)
                continue

            trading_signal = get_ai_trading_signal(latest_market, asset)
            print(f"\n📊 AI Trading Signal for {asset} ({mode}):\n{trading_signal}\n")

            time.sleep(60)  # Fetch new data every minute
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
