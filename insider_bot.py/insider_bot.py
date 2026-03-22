import requests
import pandas as pd
import time
import schedule
from datetime import datetime, timedelta
from telegram import Bot

# ====== PASTE YOUR KEYS HERE ======
import os

API_KEY = os.getenv("d6utm9pr01qig545s39gd6utm9pr01qig545s3a0")
BOT_TOKEN = os.getenv("8688735398:AAHHuNdq8_HnIdHqduuKx2JT4gT4RgOxsT8")
CHAT_ID = os.getenv("8288295007")

bot = Bot(token=BOT_TOKEN)

IMPORTANT_TITLES = ["CEO","CFO","Director","Chief","President","Chairman"]

CLUSTER_DAYS = 7
MIN_INSIDERS = 2
MIN_TOTAL_VALUE = 250000

def fetch_symbols():
    url = f"https://finnhub.io/api/v1/stock/symbol?exchange=US&token={API_KEY}"
    return [s["symbol"] for s in requests.get(url).json()]

def fetch_insider(symbol):
    url = f"https://finnhub.io/api/v1/stock/insider-transactions?symbol={symbol}&token={API_KEY}"
    return requests.get(url).json().get("data", [])

def is_important(title):
    return any(x.lower() in str(title).lower() for x in IMPORTANT_TITLES)

def detect_clusters(trades, symbol):
    if not trades:
        return None

    df = pd.DataFrame(trades)
    if df.empty:
        return None

    df["date"] = pd.to_datetime(df["transactionDate"])
    cutoff = datetime.now() - timedelta(days=CLUSTER_DAYS)

    df = df[df["date"] >= cutoff]

    if "transactionType" in df.columns:
        df = df[df["transactionType"] == "P"]

    if "position" in df.columns:
        df = df[df["position"].apply(is_important)]

    if df.empty:
        return None

    insiders = df["name"].nunique()
    total_value = df["transactionValue"].fillna(0).sum() if "transactionValue" in df.columns else 0

    if insiders >= MIN_INSIDERS and total_value >= MIN_TOTAL_VALUE:
        return {
            "symbol": symbol,
            "insiders": insiders,
            "value": total_value,
            "names": df["name"].unique()
        }

def send_alert(c):
    msg = f"""
🚨 CLUSTER BUY 🚨
Ticker: {c['symbol']}
Insiders: {c['insiders']}
Total: ${c['value']:.0f}

People:
{", ".join(c['names'])}
"""
    bot.send_message(chat_id=CHAT_ID, text=msg)

def run():
    symbols = fetch_symbols()
    print(f"Scanning {len(symbols)} stocks...")

    for s in symbols[:200]:  # start small
        print("Checking:", s)
        try:
            trades = fetch_insider(s)
            cluster = detect_clusters(trades, s)

            if cluster:
                send_alert(cluster)

            time.sleep(1)

        except Exception as e:
            print(f"Error on {s}:", e)

schedule.every(60).minutes.do(run)

run()

while True:
    schedule.run_pending()
    time.sleep(1)