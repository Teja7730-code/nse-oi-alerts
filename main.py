import requests
import pandas as pd
import time
from datetime import datetime
import pytz
from io import StringIO

TOPIC = "nseoialert"

baseline_rise = set()
baseline_slide = set()

def send_notification(message):

    requests.post(
        f"https://ntfy.sh/{TOPIC}",
        data=message.encode("utf-8")
    )

def market_open():

    india = pytz.timezone('Asia/Kolkata')

    now = datetime.now(india)

    if now.weekday() >= 5:
        return False

    current_time = now.strftime("%H:%M")

    return "09:15" <= current_time <= "15:30"

def fetch_csv(url):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    return pd.read_csv(StringIO(response.text))

def process_category(df, baseline_set, category_name):

    current_symbols = set(df["Symbol"].astype(str))

    new_symbols = current_symbols - baseline_set

    for symbol in new_symbols:

        try:

            row = df[df["Symbol"] == symbol].iloc[0]

            msg = f"""
NEW STOCK ADDED

Category:
{category_name}

Symbol: {symbol}

OI Change:
{row['%chng<br/>in OI']}%

Price Change:
{row['% CHNG in LTP']}%

LTP:
{row['LTP']}

Volume:
{row['Volume']}

Instrument:
{row['Instrument']}
"""

            print(msg)

            send_notification(msg)

        except Exception as e:
            print("Alert error:", e)

    return current_symbols

rise_url = "https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_1.csv"
slide_url = "https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_2.csv"

baseline_saved = False

while True:

    try:

        if market_open():

            rise_df = fetch_csv(rise_url)

            slide_df = fetch_csv(slide_url)

            if not baseline_saved:

                baseline_rise = set(rise_df["Symbol"].astype(str))

                baseline_slide = set(slide_df["Symbol"].astype(str))

                baseline_saved = True

                print("Morning baseline saved")

            else:

                process_category(
                    rise_df,
                    baseline_rise,
                    "Rise in OI and Rise in Price"
                )

                process_category(
                    slide_df,
                    baseline_slide,
                    "Slide in OI and Rise in Price"
                )

        else:

            print("Market closed")

    except Exception as e:

        print("Main Error:", e)

    time.sleep(60)
