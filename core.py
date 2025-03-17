import time
import requests
import pandas as pd
import ta  # Technical Analysis library

# ✅ Binance API for Spot and Futures Market Data
BINANCE_BASE_URL = "https://api.binance.com/api/v3/klines"
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"

# ✅ API Key for Exchange Rate API (Forex Data)
FOREX_API_KEY = "fa835023173c9c0014e17ba9"
FOREX_API_URL = f"https://v6.exchangerate-api.com/v6/{FOREX_API_KEY}/latest/"

# ✅ OpenRouter API Key (FREE GPT-4)
OPENROUTER_API_KEY = "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"  # Replace with your actual OpenRouter API key

# ✅ Supported Trading Assets (Spot & Futures)
CRYPTO_ASSETS = {"1": "BTCUSDT", "2": "ETHUSDT", "3": "BNBUSDT", "4": "XRPUSDT", "5": "SOLUSDT", "6": "XUSDT", "7": "LLMUSDT", "8": "MUBARAKUSDT", "9": "JELLYJELLYUSDT"}
FOREX_ASSETS = {"10": "USDJPY", "11": "EURUSD", "13": "GBPUSD", "14": "AUDUSD"}

# ✅ Fetch Crypto Market Data (Supports Spot & Futures)
def get_crypto_data(symbol="BTCUSDT", interval="1h", limit=50, is_futures=False):
    url = BINANCE_FUTURES_URL if is_futures else BINANCE_BASE_URL
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    
    try:
        response = requests.get(url, params=params)
        data = response.json()

        if not isinstance(data, list):  # Binance error response check
            print(f"⚠️ Binance API Error: {data}")
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume", "_", "_", "_", "_", "_", "_"])
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print(f"⚠️ Binance API Request Failed: {e}")
        return pd.DataFrame()

# ✅ Fetch Forex Data
def get_forex_data(symbol="USDJPY"):
    base_currency, target_currency = symbol[:3], symbol[3:]
    url = f"{FOREX_API_URL}{base_currency}"
    
    try:
        response = requests.get(url)
        data = response.json()

        if "conversion_rates" not in data:
            print(f"⚠️ Forex API Error: {data}")
            return pd.DataFrame()

        rate = data["conversion_rates"].get(target_currency)
        if rate is None:
            print(f"⚠️ Forex API did not return {target_currency} rate.")
            return pd.DataFrame()

        return pd.DataFrame({"close": [rate]})
    except Exception as e:
        print(f"⚠️ Forex API Request Failed: {e}")
        return pd.DataFrame()

# ✅ Perform Market Analysis using Technical Indicators
def analyze_market(df):
    if df.empty:
        print("⚠️ No market data available. Skipping analysis...")
        return None

    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["macd"] = ta.trend.MACD(df["close"]).macd()
    df["ema_50"] = ta.trend.EMAIndicator(df["close"], window=50).ema_indicator()
    df["ema_200"] = ta.trend.EMAIndicator(df["close"], window=200).ema_indicator()
    df["bollinger_high"] = ta.volatility.BollingerBands(df["close"]).bollinger_hband()
    df["bollinger_low"] = ta.volatility.BollingerBands(df["close"]).bollinger_lband()

    return df.iloc[-1]  # Get latest market data

# ✅ AI-Powered Trading Signal (Using OpenRouter)
def get_ai_trading_signal(market_data, asset, is_futures=False):
    if market_data is None:
        return "⚠️ No market data available for AI analysis."

    trade_type = "Futures" if is_futures else "Spot"
    prompt = f"""
    Given the following {trade_type} trading market conditions for {asset}:
    - RSI: {market_data['rsi']}
    - MACD: {market_data['macd']}
    - EMA-50: {market_data['ema_50']}
    - EMA-200: {market_data['ema_200']}
    - Bollinger Bands: High {market_data['bollinger_high']}, Low {market_data['bollinger_low']}
    
    Predict the best trade signal (Buy, Sell, Hold) with Entry, Stop Loss, and Take Profit. 
    Return result in JSON format:

    {{
      "signal": "",
      "entry": "",
      "stop_loss": "",    
      "take_profit": "",  
      "asset": "{asset}"
    }}
    """

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "open-r1/olympiccoder-7b:free",
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
    print("\n📌 Select a Trading Pair:")
    for key, value in {**CRYPTO_ASSETS, **FOREX_ASSETS}.items():
        print(f"{key} - {value}")

    choice = input("\nEnter the option number: ")
    asset = {**CRYPTO_ASSETS, **FOREX_ASSETS}.get(choice)

    if not asset:
        print("⚠️ Invalid selection. Exiting.")
        return

    is_crypto = choice in CRYPTO_ASSETS.keys()
    is_futures = False

    if is_crypto:
        trade_type = input("Select trading mode: (1) Spot (2) Futures: ").strip()
        is_futures = trade_type == "2"

    print(f"\n📊 Fetching real-time data for {asset} ({'Futures' if is_futures else 'Spot'})...")

    while True:
        try:
            market_data = get_crypto_data(asset, is_futures=is_futures) if is_crypto else get_forex_data(asset)
            if market_data.empty:
                print("⚠️ No market data found. Retrying in 10 seconds...")
                time.sleep(10)
                continue  # Skip this loop if no data

            latest_market = analyze_market(market_data)
            if latest_market is None:
                time.sleep(10)
                continue

            trading_signal = get_ai_trading_signal(latest_market, asset, is_futures)
            print(f"\n📊 AI Trading Signal for {asset} ({'Futures' if is_futures else 'Spot'}):\n{trading_signal}\n")

            choice = input("Do you want to fetch another signal? (y/n): ").strip().lower()
            if choice != 'y':
                break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
