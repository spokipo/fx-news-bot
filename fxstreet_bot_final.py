import os
import asyncio
import cloudscraper
from bs4 import BeautifulSoup
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# === НАСТРОЙКИ из .env ===
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MESSAGE_THREAD_ID = int(os.getenv("MESSAGE_THREAD_ID", 0))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))

bot = Bot(token=TELEGRAM_BOT_TOKEN)
last_link = None
first_run = True

# === СБОР НОВОСТЕЙ ===
def get_latest_news():
    print("📡 Получаем страницу новостей...", flush=True)

    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get("https://www.fxstreet.ru.com/news", timeout=10)

        if response.status_code != 200:
            print(f"❌ Ошибка загрузки страницы: {response.status_code}", flush=True)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        news_tags = soup.select("div.fxs_latestNews .fxs_headline_medium a")

        print(f"🔍 Найдено новостей: {len(news_tags)}", flush=True)

        for tag in news_tags:
            href = tag.get("href")
            title = tag.get_text(strip=True)

            if not href or not title:
                continue

            if "/news/" not in href:
                continue

            link = href if href.startswith("http") else "https://www.fxstreet.ru.com" + href
            print(f"🆕 Найдена новость: {title} | {link}", flush=True)
            return {"title": title, "url": link}

        print("⚠️ Подходящих новостей не найдено", flush=True)
        return None

    except Exception as e:
        print("❌ Ошибка в get_latest_news():", e, flush=True)
        return None

# === ОТПРАВКА В ТЕЛЕГРАМ ===
async def send_news(news):
    global last_link, first_run

    if not news:
        return

    if news["url"] == last_link:
        print("🔁 Новость уже была отправлена", flush=True)
        return

    msg = f"📰 <b>{news['title']}</b>\n{news['url']}"

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=msg,
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
        print("✅ Новость отправлена", flush=True)
        last_link = news["url"]
    except Exception as e:
        print("❌ Ошибка при отправке в Telegram:", e, flush=True)

    if first_run:
        first_run = False

# === ОСНОВНОЙ ЦИКЛ ===
async def main():
    global first_run

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="🤖 Бот запущен и следит за лентой FXStreet",
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
    except Exception as e:
        print("❌ Ошибка при запуске бота:", e, flush=True)

    while True:
        try:
            news = get_latest_news()
            await send_news(news)
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            print("❌ Ошибка в основном цикле:", e, flush=True)
            await asyncio.sleep(30)

# === HTTP-СЕРВЕР ДЛЯ RENDER ===
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running.")

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    print("🌐 HTTP-сервер запущен на порту 10000", flush=True)
    server.serve_forever()

# === ЗАПУСК ===
if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    asyncio.run(main())
