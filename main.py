import requests

TOPIC = "nseoialert"

def send_notification(message):

    requests.post(
        f"https://ntfy.sh/{TOPIC}",
        data=message.encode("utf-8")
    )

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com/",
    "Accept-Language": "en-US,en;q=0.9"
}

try:

    session = requests.Session()

    # Open homepage first
    session.get(
        "https://www.nseindia.com",
        headers=headers,
        timeout=30
    )

    # NSE OI Spurts API
    url = "https://www.nseindia.com/api/live-analysis-oi-spurts-underlyings"

    response = session.get(
        url,
        headers=headers,
        timeout=30
    )

    data = response.json()

    message = "NSE OI LIVE DATA\n\n"

    count = 0

    for item in data["data"]:

        symbol = item.get("symbol", "")

        oi_change = item.get("oiChangePerc", "")

        price_change = item.get("futPriceChangePerc", "")

        ltp = item.get("latestOI", "")

        message += (
            f"{symbol}\n"
            f"OI Change: {oi_change}%\n"
            f"Price Change: {price_change}%\n"
            f"OI: {ltp}\n\n"
        )

        count += 1

        if count >= 10:
            break

    send_notification(message)

except Exception as e:

    send_notification(f"ERROR\n\n{e}")
