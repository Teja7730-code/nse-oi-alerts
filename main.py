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

    url = "https://www.nseindia.com/market-data/oi-spurts"

    response = requests.get(url, headers=headers, timeout=30)

    soup = BeautifulSoup(response.text, "lxml")

    title = soup.title.string if soup.title else "No Title"

    send_notification(
        f"NSE CHECK WORKING\n\nPage Title:\n{title}"
    )

except Exception as e:

    send_notification(f"ERROR\n\n{e}")
