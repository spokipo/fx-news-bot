import requests
from bs4 import BeautifulSoup
import time
import asyncio
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = "8374044886:AAHaI_LNKeW90A5sOYA_uzs5nfxVWBoM2us"
TELEGRAM_CHAT_ID = "-1002518445518"
MESSAGE_THREAD_ID = 15998
CHECK_INTERVAL = 60  # интервал проверки новостей в секундах

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# === ХРАНЕНИЕ ОТПРАВЛЕННЫХ ССЫЛОК ===
LINKS_FILE = "sent_links.txt"
if os.path.exists(LINKS_FILE):
    with open(LINKS_FILE, "r") as f:
        posted_links = set(line.strip() for line in f if line.strip())
else:
    posted_links = set()

# === СБОР НОВОСТЕЙ ===
def get_news():
    url = "https://www.fxstreet.ru.com/news"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        news_items = soup.select("div.news-feed__item a")
        news = []
        for el in news_items:
            title = el.get_text(strip=True)
            href = el.get("href")
            if href and not href.startswith("http"):
                link = "https://www.fxstreet.ru.com" + href
            else:
                link = href
            if title and link and link not in posted_links:
                news.append((title, link))
        return news
    except Exception as e:
        print("Ошибка при получении новостей:", e)
        return []

# === ОТПРАВКА В ТЕЛЕГРАМ ===
async def send_news(news_list):
    for title, link in news_list:
        if link in posted_links:
            continue
        msg = f"📰 <b>{title}</b>\n{link}"
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode="HTML",
                message_thread_id=MESSAGE_THREAD_ID
            )
            posted_links.add(link)
            with open(LINKS_FILE, "a") as f:
                f.write(link + "\n")
            await asyncio.sleep(1)  # чуть-чуть подождать между сообщениями
        except Exception as e:
            print("Ошибка отправки:", e)

# === ОСНОВНОЙ ЦИКЛ ===
async def main():
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="🚀 Бот запущен и следит за новостями FXStreet",
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
    except Exception as e:
        print("Ошибка при запуске бота:", e)

    while True:
        try:
            news = get_news()
            if news:
                await send_news(news)
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            print("Ошибка цикла:", e)
            await asyncio.sleep(30)

# === HTTP СЕРВЕР ДЛЯ RENDER ===
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running.")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    print("HTTP-сервер запущен на порту 10000")
    server.serve_forever()

# === ЗАПУСК ===
if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    asyncio.run(main())
