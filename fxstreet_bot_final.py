import requests
from bs4 import BeautifulSoup
import time
import asyncio
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = "8374044886:AAHaI_LNKeW90A5sOYA_uzs5nfxVWBoM2us"
TELEGRAM_CHAT_ID = "-2518445518"
MESSAGE_THREAD_ID = 15998
CHECK_INTERVAL = 60  # в секундах

bot = Bot(token=TELEGRAM_BOT_TOKEN)
posted_links = set()

def get_news():
    url = "https://www.fxstreet.ru.com/news"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    news_items = soup.select("div.news-feed__item, article, a")
    news = []
    for el in news_items:
        title_tag = el.select_one("a") or el
        title = title_tag.get_text(strip=True)
        href = title_tag.get("href")
        if href and "http" not in href:
            link = "https://www.fxstreet.ru.com" + href
        else:
            link = href
        if title and link and link not in posted_links:
            news.append((title, link))
    return news

async def send_news(news_list):
    for title, link in news_list:
        msg = f"📰 <b>{title}</b>\n{link}"
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode="HTML",
                message_thread_id=MESSAGE_THREAD_ID
            )
            posted_links.add(link)
        except Exception as e:
            print("Ошибка отправки:", e)

async def main():
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="🚀 Бот запущен и готов к работе!",
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
    except Exception as e:
        print("Ошибка при отправке теста:", e)

    while True:
        try:
            news = get_news()
            if news:
                await send_news(news)
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            print("Ошибка цикла:", e)
            await asyncio.sleep(30)

# === ФИКТИВНЫЙ СЕРВЕР ДЛЯ RENDER ===
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running.")

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    print("Запущен фиктивный HTTP-сервер на порту 10000")
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    asyncio.run(main())
