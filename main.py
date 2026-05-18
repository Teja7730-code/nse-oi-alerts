import requests
import time
from datetime import datetime
import pytz

TOPIC = "nseoialert"

API_URL = "https://www.nseindia.com/api/live-analysis-oi-spurts-contracts"

# ===== INDEX FILTER =====
IGNORE_SYMBOLS = [
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY",
    "MIDCPNIFTY",
    "SENSEX",
    "BANKEX"
]

# ===== SETTINGS =====
MIN_OI_CHANGE = 10
MIN_PRICE_CHANGE = 0.5

# ===== STORAGE =====
baseline_rr = set()
baseline_sr = set()

appearance_count = {}

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

# ===== SESSION =====
session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/"
}

# ===== CREATE NSE SESSION =====
try:

    session.get(
        "https://www.nseindia.com",
        headers=headers,
        timeout=20
    )

    time.sleep(3)

    session.get(
        "https://www.nseindia.com/market-data/oi-spurts",
        headers=headers,
        timeout=20
    )

    print("NSE Session Ready")

except Exception as e:

    print("Session Error:", e)

# ===== FILTER STOCKS =====
def filter_rows(rows):

    filtered = []

    for row in rows:

        try:

            symbol = str(row.get("symbol", "")).upper()

            ignore = False

            for idx in IGNORE_SYMBOLS:

                if idx in symbol:
                    ignore = True
                    break

            if ignore:
                continue

            oi_change = float(row.get("pChangeInOI", 0))

            price_change = float(row.get("pChange", 0))

            if oi_change < MIN_OI_CHANGE:
                continue

            if price_change < MIN_PRICE_CHANGE:
                continue

            filtered.append(row)

        except:
            pass

    return filtered

# ===== FETCH DATA =====
def fetch_data():

    response = session.get(
        API_URL,
        headers=headers,
        timeout=20
    )

    print("Status Code:", response.status_code)

    if response.status_code != 200:

        raise Exception(f"NSE API Failed: {response.status_code}")

    data = response.json()

    rr = data["data"][2]["Rise-in-OI-Rise"]

    sr = data["data"][1]["Slide-in-OI-Rise"]

    rr = filter_rows(rr)
    sr = filter_rows(sr)

    return rr, sr

# ===== FORMAT MESSAGE =====
def format_message(title, rows):

    msg = f"{title}\n\n"

    count = 0

    for row in rows:

        try:

            symbol = row.get("symbol", "")

            expiry = row.get("expiryDate", "")

            strike = row.get("strikePrice", "")

            option_type = row.get("optionType", "")

            oi = row.get("pChangeInOI", "")

            price = row.get("pChange", "")

            ltp = row.get("ltp", "")

            instrument = row.get("instrument", "")

            volume = row.get("volume", "")

            msg += (
                f"Symbol: {symbol}\n"
                f"Expiry: {expiry}\n"
                f"Strike: {strike}\n"
                f"Type: {option_type}\n"
                f"Instrument: {instrument}\n"
                f"OI Change: {oi}%\n"
                f"Price Change: {price}%\n"
                f"LTP: {ltp}\n"
                f"Volume: {volume}\n\n"
            )

            count += 1

            if count >= 10:
                break

        except:
            pass

    return msg

# ===== PROCESS NEW STOCKS =====
def process_new(rows, baseline, category):

    current = set()

    for row in rows:

        try:

            key = row["identifier"]

            current.add(key)

            symbol = row.get("symbol", "")

            # ===== REPEATED APPEARANCE =====
            if symbol not in appearance_count:
                appearance_count[symbol] = 1
            else:
                appearance_count[symbol] += 1

            repeat_count = appearance_count[symbol]

            # ===== ONLY ALERT NEW ENTRIES =====
            if key not in baseline:

                expiry = row.get("expiryDate", "")

                strike = row.get("strikePrice", "")

                option_type = row.get("optionType", "")

                oi = row.get("pChangeInOI", "")

                price = row.get("pChange", "")

                ltp = row.get("ltp", "")

                instrument = row.get("instrument", "")

                volume = row.get("volume", "")

                confidence = "MEDIUM"

                if repeat_count >= 3:
                    confidence = "HIGH"

                if repeat_count >= 5:
                    confidence = "VERY HIGH"

                msg = (
                    f"NEW MOMENTUM ALERT\n\n"
                    f"Category:\n{category}\n\n"
                    f"Confidence: {confidence}\n"
                    f"Repeated Appearance: {repeat_count}\n\n"
                    f"Symbol: {symbol}\n"
                    f"Expiry: {expiry}\n"
                    f"Strike: {strike}\n"
                    f"Type: {option_type}\n"
                    f"Instrument: {instrument}\n\n"
                    f"OI Change: {oi}%\n"
                    f"Price Change: {price}%\n"
                    f"LTP: {ltp}\n"
                    f"Volume: {volume}"
                )

                print(msg)

                send_notification(msg)

        except Exception as e:

            print("Process Error:", e)

    return current

# ===== BOT START =====
send_notification("ADVANCED NSE STOCK OI BOT STARTED")

# ===== MAIN LOOP =====
while True:

    try:

        now = india_time()

        current_time = now.strftime("%H:%M")

        print("Running:", current_time)

        rr, sr = fetch_data()

        # ===== MORNING SUMMARY =====
        if current_time >= "09:15" and not morning_sent:

            baseline_rr = set(x["identifier"] for x in rr)
            baseline_sr = set(x["identifier"] for x in sr)

            send_notification(
                format_message(
                    "09:15 AM\nRise in OI + Rise in Price",
                    rr
                )
            )

            time.sleep(2)

            send_notification(
                format_message(
                    "09:15 AM\nSlide in OI + Rise in Price",
                    sr
                )
            )

            morning_sent = True

            print("Morning Summary Sent")

        # ===== LIVE ALERTS =====
        if market_open():

            baseline_rr = process_new(
                rr,
                baseline_rr,
                "Rise in OI + Rise in Price"
            )

            baseline_sr = process_new(
                sr,
                baseline_sr,
                "Slide in OI + Rise in Price"
            )

        # ===== CLOSING SUMMARY =====
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
                    "03:30 PM CLOSE\nSlide in OI + Rise in Price",
                    sr
                )
            )

            closing_sent = True

            print("Closing Summary Sent")

    except Exception as e:

        print("MAIN ERROR:", e)

        send_notification(f"ERROR\n\n{e}")

    time.sleep(60)
