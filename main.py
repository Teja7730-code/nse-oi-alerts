import requests
from bs4 import BeautifulSoup

TOPIC = "nseoialert"

def send_notification(message):

    requests.post(
        f"https://ntfy.sh/{TOPIC}",
        data=message.encode("utf-8")
    )

headers = {
    "User-Agent": "Mozilla/5.0"
}

try:

    session = requests.Session()

    # Open NSE homepage first
    session.get(
        "https://www.nseindia.com",
        headers=headers,
        timeout=30
    )

    # Open OI Spurts page
    response = session.get(
        "https://www.nseindia.com/market-data/oi-spurts",
        headers=headers,
        timeout=30
    )

    soup = BeautifulSoup(response.text, "lxml")

    rows = soup.select("table tbody tr")

    message = "NSE OI DATA TEST\n\n"

    count = 0

    for row in rows:

        cols = row.find_all("td")

        if len(cols) >= 8:

            symbol = cols[1].get_text(strip=True)

            ltp = cols[5].get_text(strip=True)

            oi_change = cols[6].get_text(strip=True)

            price_change = cols[7].get_text(strip=True)

            message += (
                f"{symbol}\n"
                f"LTP: {ltp}\n"
                f"OI: {oi_change}\n"
                f"Price: {price_change}\n\n"
            )

            count += 1

        if count >= 10:
            break

    if count == 0:

        message += "No rows found"

    send_notification(message)

except Exception as e:

    send_notification(f"ERROR\n\n{e}")
