import os
import asyncio
import cloudscraper
from bs4 import BeautifulSoup
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# === Настройки из переменных окружения (.env или Render) ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MESSAGE_THREAD_ID = int(os.getenv("MESSAGE_THREAD_ID", 0))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))

bot = Bot(token=BOT_TOKEN)
last_link = None
first_run = True

# === Получение свежих новостей с Investing.com ===
def get_forex_news():
    print("📡 Получаем новости с Investing.com...", flush=True)

    try:
        scraper = cloudscraper.create_scraper()
        url = "https://ru.investing.com/news/forex-news"
        response = scraper.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})

        if response.status_code != 200:
            print(f"❌ Ошибка загрузки: {response.status_code}", flush=True)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.select("section[data-test='left-column'] article")

        news = []
        for art in articles:
            a_tag = art.find("a", href=True)
            title = a_tag.get_text(strip=True) if a_tag else None
            href = a_tag["href"] if a_tag else None

            if title and href and "/news/" in href:
                full_link = "https://ru.investing.com" + href
                news.append((title, full_link))

        print(f"🔍 Найдено новостей: {len(news)}", flush=True)
        return news

    except Exception as e:
        print("❌ Ошибка при получении новостей:", e, flush=True)
        return []

# === Отправка новости в Telegram ===
async def send_news(news_list):
    global last_link, first_run

    for title, link in reversed(news_list):  # от старых к новым
        if link == last_link:
            continue

        msg = f"📰 <b>{title}</b>\n{link}"
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode="HTML",
                message_thread_id=MESSAGE_THREAD_ID
            )
            print(f"✅ Отправлено: {title}", flush=True)
            last_link = link
            if first_run:
                break  # отправим только одну при первом запуске
        except Exception as e:
            print("❌ Ошибка отправки:", e, flush=True)

    first_run = False

# === Основной цикл ===
async def main():
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="🤖 Бот по Investing.com Forex запущен",
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
    except Exception as e:
        print("❌ Ошибка при запуске бота:", e, flush=True)

    while True:
        try:
            news = get_forex_news()
            await send_news(news)
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            print("❌ Ошибка в основном цикле:", e, flush=True)
            await asyncio.sleep(30)

# === HTTP-сервер для Render ===
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running.")

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    print("🌐 HTTP-сервер запущен на порту 10000", flush=True)
    server.serve_forever()

# === Запуск ===
if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    asyncio.run(main())
