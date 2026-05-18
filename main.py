import requests
import pandas as pd
import time
from datetime import datetime
import pytz
from io import StringIO

TOPIC = "nseoialert"

# ===== STORAGE =====
baseline_rise = set()
baseline_slide = set()

already_alerted_rise = set()
already_alerted_slide = set()

morning_sent = False
closing_sent = False

# ===== CSV URLS =====
rise_url = "https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_1.csv"

slide_url = "https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_2.csv"

# ===== NOTIFICATION =====
def send_notification(message):

    requests.post(
        f"https://ntfy.sh/{TOPIC}",
        data=message.encode("utf-8")
    )

# ===== CURRENT TIME =====
def get_india_time():

    india = pytz.timezone("Asia/Kolkata")

    return datetime.now(india)

# ===== MARKET TIME =====
def market_open():

    now = get_india_time()

    if now.weekday() >= 5:
        return False

    current_time = now.strftime("%H:%M")

    return "09:15" <= current_time <= "15:30"

# ===== FETCH CSV =====
def fetch_csv(url):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    return pd.read_csv(StringIO(response.text))

# ===== FORMAT SUMMARY =====
def create_summary(df, title):

    message = f"{title}\n\n"

    for _, row in df.iterrows():

        try:

            symbol = str(row["Symbol"])

            oi_change = str(row["%chng<br/>in OI"])

            price_change = str(row["% CHNG in LTP"])

            ltp = str(row["LTP"])

            message += (
                f"{symbol}\n"
                f"OI: {oi_change}%\n"
                f"Price: {price_change}%\n"
                f"LTP: {ltp}\n\n"
            )

        except:
            pass

    return message

# ===== PROCESS NEW STOCKS =====
def process_new_stocks(df, baseline_set, alerted_set, category_name):

    current_symbols = set(df["Symbol"].astype(str))

    new_symbols = current_symbols - baseline_set

    for symbol in new_symbols:

        if symbol not in alerted_set:

            try:

                row = df[df["Symbol"] == symbol].iloc[0]

                msg = (
                    f"NEW STOCK ADDED\n\n"
                    f"Category:\n{category_name}\n\n"
                    f"Symbol: {symbol}\n\n"
                    f"OI Change: {row['%chng<br/>in OI']}%\n"
                    f"Price Change: {row['% CHNG in LTP']}%\n"
                    f"LTP: {row['LTP']}\n"
                    f"Volume: {row['Volume']}"
                )

                print(msg)

                send_notification(msg)

                alerted_set.add(symbol)

            except Exception as e:

                print("Alert Error:", e)

# ===== TEST CURRENT MARKET CLOSE SUMMARY =====
try:

    rise_df = fetch_csv(rise_url)

    slide_df = fetch_csv(slide_url)

    rise_summary = create_summary(
        rise_df,
        "03:30 PM CLOSE\nRise in OI and Rise in Price\n"
    )

    slide_summary = create_summary(
        slide_df,
        "03:30 PM CLOSE\nSlide in OI and Rise in Price\n"
    )

    send_notification(rise_summary)

    time.sleep(2)

    send_notification(slide_summary)

except Exception as e:

    send_notification(f"TEST ERROR\n{e}")

# ===== MAIN LOOP =====
while True:

    try:

        now = get_india_time()

        current_time = now.strftime("%H:%M")

        rise_df = fetch_csv(rise_url)

        slide_df = fetch_csv(slide_url)

        # ===== MORNING SUMMARY =====
        if current_time >= "09:15" and not morning_sent:

            baseline_rise = set(rise_df["Symbol"].astype(str))
            baseline_slide = set(slide_df["Symbol"].astype(str))

            rise_summary = create_summary(
                rise_df,
                "09:15 AM\nRise in OI and Rise in Price\n"
            )

            slide_summary = create_summary(
                slide_df,
                "09:15 AM\nSlide in OI and Rise in Price\n"
            )

            send_notification(rise_summary)

            time.sleep(2)

            send_notification(slide_summary)

            morning_sent = True

            print("Morning summary sent")

        # ===== LIVE MARKET =====
        if market_open():

            process_new_stocks(
                rise_df,
                baseline_rise,
                already_alerted_rise,
                "Rise in OI and Rise in Price"
            )

            process_new_stocks(
                slide_df,
                baseline_slide,
                already_alerted_slide,
                "Slide in OI and Rise in Price"
            )

        # ===== MARKET CLOSE SUMMARY =====
        if current_time >= "15:30" and not closing_sent:

            rise_summary = create_summary(
                rise_df,
                "03:30 PM CLOSE\nRise in OI and Rise in Price\n"
            )

            slide_summary = create_summary(
                slide_df,
                "03:30 PM CLOSE\nSlide in OI and Rise in Price\n"
            )

            send_notification(rise_summary)

            time.sleep(2)

            send_notification(slide_summary)

            closing_sent = True

            print("Closing summary sent")

    except Exception as e:

        print("MAIN ERROR:", e)

    time.sleep(60)
