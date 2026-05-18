import requests
import time
from datetime import datetime
import pytz

TOPIC = "nseoialert"

API_URL = "https://www.nseindia.com/api/live-analysis-oi-spurts-contracts"

# ===== STORAGE =====
baseline_rr = set()
baseline_rs = set()
baseline_sr = set()
baseline_ss = set()

morning_sent = False
closing_sent = False

# ===== NOTIFICATION =====
def send_notification(message):

    try:

        requests.post(
            f"https://ntfy.sh/{TOPIC}",
            data=message.encode("utf-8"),
            timeout=10
        )

        print("Notification Sent")

    except Exception as e:

        print("Notification Error:", e)

# ===== INDIA TIME =====
def india_time():

    india = pytz.timezone("Asia/Kolkata")

    return datetime.now(india)

# ===== MARKET HOURS =====
def market_open():

    now = india_time()

    if now.weekday() >= 5:
        return False

    current = now.strftime("%H:%M")

    return "09:15" <= current <= "15:30"

# ===== NSE SESSION =====
session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json"
}

session.get("https://www.nseindia.com", headers=headers)

# ===== FETCH DATA =====
def fetch_data():

    response = session.get(
        API_URL,
        headers=headers,
        timeout=20
    )

    data = response.json()

    rr = data["data"][2]["Rise-in-OI-Rise"]

    rs = data["data"][3]["Rise-in-OI-Slide"]

    sr = data["data"][1]["Slide-in-OI-Rise"]

    ss = data["data"][0]["Slide-in-OI-Slide"]

    return rr, rs, sr, ss

# ===== FORMAT DATA =====
def format_message(title, rows):

    msg = f"{title}\n\n"

    for row in rows[:20]:

        try:

            symbol = row["symbol"]

            price = row["pChange"]

            oi = row["pChangeInOI"]

            ltp = row["ltp"]

            instrument = row["instrument"]

            msg += (
                f"{symbol}\n"
                f"{instrument}\n"
                f"Price: {price}%\n"
                f"OI: {oi}%\n"
                f"LTP: {ltp}\n\n"
            )

        except:
            pass

    return msg

# ===== NEW STOCK ALERT =====
def process_new(rows, baseline, category):

    current = set()

    for row in rows:

        try:

            key = row["identifier"]

            current.add(key)

            if key not in baseline:

                symbol = row["symbol"]

                instrument = row["instrument"]

                price = row["pChange"]

                oi = row["pChangeInOI"]

                ltp = row["ltp"]

                volume = row["volume"]

                msg = (
                    f"NEW ENTRY DETECTED\n\n"
                    f"Category:\n{category}\n\n"
                    f"Symbol: {symbol}\n"
                    f"{instrument}\n\n"
                    f"Price Change: {price}%\n"
                    f"OI Change: {oi}%\n"
                    f"LTP: {ltp}\n"
                    f"Volume: {volume}"
                )

                print(msg)

                send_notification(msg)

        except Exception as e:

            print("Process Error:", e)

    return current

# ===== START =====
send_notification("NSE OI ALERT SYSTEM STARTED")

# ===== MAIN LOOP =====
while True:

    try:

        now = india_time()

        current_time = now.strftime("%H:%M")

        rr, rs, sr, ss = fetch_data()

        # ===== 09:15 MORNING DATA =====
        if current_time >= "09:15" and not morning_sent:

            baseline_rr = set(x["identifier"] for x in rr)
            baseline_rs = set(x["identifier"] for x in rs)
            baseline_sr = set(x["identifier"] for x in sr)
            baseline_ss = set(x["identifier"] for x in ss)

            send_notification(
                format_message(
                    "09:15 AM\nRise in OI + Rise in Price",
                    rr
                )
            )

            time.sleep(2)

            send_notification(
                format_message(
                    "09:15 AM\nRise in OI + Slide in Price",
                    rs
                )
            )

            time.sleep(2)

            send_notification(
                format_message(
                    "09:15 AM\nSlide in OI + Rise in Price",
                    sr
                )
            )

            time.sleep(2)

            send_notification(
                format_message(
                    "09:15 AM\nSlide in OI + Slide in Price",
                    ss
                )
            )

            morning_sent = True

            print("Morning Summary Sent")

        # ===== LIVE MARKET =====
        if market_open():

            baseline_rr = process_new(
                rr,
                baseline_rr,
                "Rise in OI + Rise in Price"
            )

            baseline_rs = process_new(
                rs,
                baseline_rs,
                "Rise in OI + Slide in Price"
            )

            baseline_sr = process_new(
                sr,
                baseline_sr,
                "Slide in OI + Rise in Price"
            )

            baseline_ss = process_new(
                ss,
                baseline_ss,
                "Slide in OI + Slide in Price"
            )

        # ===== 03:30 PM CLOSING =====
        if current_time >= "15:30" and not closing_sent:

            send_notification(
                format_message(
                    "03:30 PM CLOSE\nRise in OI + Rise in Price",
                    rr
                )
            )

            time.sleep(2)

            send_notification(
                format_message(
                    "03:30 PM CLOSE\nRise in OI + Slide in Price",
                    rs
                )
            )

            time.sleep(2)

            send_notification(
                format_message(
                    "03:30 PM CLOSE\nSlide in OI + Rise in Price",
                    sr
                )
            )

            time.sleep(2)

            send_notification(
                format_message(
                    "03:30 PM CLOSE\nSlide in OI + Slide in Price",
                    ss
                )
            )

            closing_sent = True

            print("Closing Summary Sent")

    except Exception as e:

        print("MAIN ERROR:", e)

    time.sleep(60)
