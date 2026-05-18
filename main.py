from playwright.sync_api import sync_playwright
import requests
import time
from datetime import datetime
import pytz

TOPIC = "nseoialert"

# ===== STORAGE =====
baseline_rise = set()
baseline_slide = set()

already_alerted_rise = set()
already_alerted_slide = set()

morning_sent = False
closing_sent = False

# ===== SEND NOTIFICATION =====
def send_notification(message):

    try:

        requests.post(
            f"https://ntfy.sh/{TOPIC}",
            data=message.encode("utf-8"),
            timeout=10
        )

    except Exception as e:

        print("Notification Error:", e)

# ===== INDIA TIME =====
def get_india_time():

    india = pytz.timezone("Asia/Kolkata")

    return datetime.now(india)

# ===== MARKET HOURS =====
def market_open():

    now = get_india_time()

    if now.weekday() >= 5:
        return False

    current_time = now.strftime("%H:%M")

    return "09:15" <= current_time <= "15:30"

# ===== FETCH CATEGORY DATA =====
def fetch_category_data(page, category_name):

    data = []

    try:

        # Open dropdown safely
        dropdown = page.locator("select")

        dropdown.first.select_option(label=category_name)

        page.wait_for_timeout(5000)

        rows = page.locator("table tbody tr")

        count = rows.count()

        print(f"{category_name} rows:", count)

        for i in range(count):

            try:

                cols = rows.nth(i).locator("td")

                total_cols = cols.count()

                if total_cols < 8:
                    continue

                symbol = cols.nth(1).inner_text().strip()

                ltp = cols.nth(5).inner_text().strip()

                oi_change = cols.nth(6).inner_text().strip()

                price_change = cols.nth(7).inner_text().strip()

                volume = cols.nth(4).inner_text().strip()

                if symbol:

                    data.append({
                        "symbol": symbol,
                        "oi_change": oi_change,
                        "price_change": price_change,
                        "ltp": ltp,
                        "volume": volume
                    })

            except Exception as row_error:

                print("Row Error:", row_error)

    except Exception as e:

        print("Category Fetch Error:", e)

    return data

# ===== SUMMARY =====
def create_summary(data, title):

    msg = f"{title}\n\n"

    if not data:

        msg += "No data found"

        return msg

    for item in data[:20]:

        msg += (
            f"{item['symbol']}\n"
            f"OI: {item['oi_change']}\n"
            f"Price: {item['price_change']}\n"
            f"LTP: {item['ltp']}\n\n"
        )

    return msg

# ===== PROCESS NEW STOCKS =====
def process_new_stocks(data, baseline_set, alerted_set, category_name):

    current_symbols = set()

    for item in data:

        current_symbols.add(item["symbol"])

    new_symbols = current_symbols - baseline_set

    for item in data:

        symbol = item["symbol"]

        if symbol in new_symbols and symbol not in alerted_set:

            msg = (
                f"NEW STOCK ADDED\n\n"
                f"Category:\n{category_name}\n\n"
                f"Symbol: {symbol}\n\n"
                f"OI Change: {item['oi_change']}\n"
                f"Price Change: {item['price_change']}\n"
                f"LTP: {item['ltp']}\n"
                f"Volume: {item['volume']}"
            )

            print(msg)

            send_notification(msg)

            alerted_set.add(symbol)

# ===== PLAYWRIGHT =====
with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage"
        ]
    )

    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36"
    )

    page.goto(
        "https://www.nseindia.com/market-data/oi-spurts",
        timeout=120000
    )

    page.wait_for_timeout(10000)

    # ===== TEST NOTIFICATION =====
    send_notification("NSE ALERT SYSTEM STARTED")

    # ===== MAIN LOOP =====
    while True:

        try:

            now = get_india_time()

            current_time = now.strftime("%H:%M")

            print("Running:", current_time)

            rise_data = fetch_category_data(
                page,
                "Rise in OI and Rise in Price"
            )

            slide_data = fetch_category_data(
                page,
                "Slide in OI and Rise in Price"
            )

            # ===== MORNING SUMMARY =====
            if current_time >= "09:15" and not morning_sent:

                baseline_rise = set(
                    [x["symbol"] for x in rise_data]
                )

                baseline_slide = set(
                    [x["symbol"] for x in slide_data]
                )

                send_notification(
                    create_summary(
                        rise_data,
                        "09:15 AM\nRise in OI and Rise in Price"
                    )
                )

                time.sleep(2)

                send_notification(
                    create_summary(
                        slide_data,
                        "09:15 AM\nSlide in OI and Rise in Price"
                    )
                )

                morning_sent = True

                print("Morning summary sent")

            # ===== LIVE ALERTS =====
            if market_open():

                process_new_stocks(
                    rise_data,
                    baseline_rise,
                    already_alerted_rise,
                    "Rise in OI and Rise in Price"
                )

                process_new_stocks(
                    slide_data,
                    baseline_slide,
                    already_alerted_slide,
                    "Slide in OI and Rise in Price"
                )

            # ===== MARKET CLOSE =====
            if current_time >= "15:30" and not closing_sent:

                send_notification(
                    create_summary(
                        rise_data,
                        "03:30 PM CLOSE\nRise in OI and Rise in Price"
                    )
                )

                time.sleep(2)

                send_notification(
                    create_summary(
                        slide_data,
                        "03:30 PM CLOSE\nSlide in OI and Rise in Price"
                    )
                )

                closing_sent = True

                print("Closing summary sent")

        except Exception as e:

            print("MAIN LOOP ERROR:", e)

            send_notification(f"ERROR\n{e}")

        time.sleep(60)
