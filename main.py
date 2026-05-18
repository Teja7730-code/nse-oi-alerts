from playwright.sync_api import sync_playwright
import requests
import time
from datetime import datetime
import pytz

TOPIC = "nseoialert"

previous_symbols = set()

def send_notification(message):
    requests.post(
        f"https://ntfy.sh/{TOPIC}",
        data=message.encode("utf-8")
    )

def market_open():

    india = pytz.timezone('Asia/Kolkata')

    now = datetime.now(india)

    # Saturday = 5, Sunday = 6
    if now.weekday() >= 5:
        return False

    current_time = now.strftime("%H:%M")

    return "09:15" <= current_time <= "15:30"

def fetch_symbols():

    symbols = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        page.goto("https://www.nseindia.com/market-data/oi-spurts")

        page.wait_for_timeout(8000)

        rows = page.locator("table tbody tr")

        count = rows.count()

        for i in range(count):

            try:
                symbol = rows.nth(i).locator("td").nth(1).inner_text()

                if symbol.strip():
                    symbols.append(symbol.strip())

            except:
                pass

        browser.close()

    return symbols


# TEST NOTIFICATION
send_notification("TEST ALERT WORKING")


while True:

    try:

        if market_open():

            current_symbols = set(fetch_symbols())

            new_symbols = current_symbols - previous_symbols

            if previous_symbols:

                for symbol in new_symbols:

                    msg = f"NEW STOCK DETECTED\n\n{symbol}"

                    print(msg)

                    send_notification(msg)

            previous_symbols = current_symbols

        else:
            print("Market closed")

    except Exception as e:

        print("Error:", e)

    time.sleep(60)
