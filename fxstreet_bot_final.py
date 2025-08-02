import asyncio
import cloudscraper
from bs4 import BeautifulSoup
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")
MESSAGE_THREAD_ID = int(os.getenv("MESSAGE_THREAD_ID", "0"))
CHECK_INTERVAL = 60  # в секундах

bot = Bot(token=TELEGRAM_BOT_TOKEN)
last_sent_link = None

# === ПОЛУЧЕНИЕ ПОСЛЕДНЕЙ НОВОСТИ ===
def get_latest_news():
    print("📡 Получаем страницу новостей...", flush=True)

    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get("https://www.fxstreet.ru.com/news", timeout=10)

        if response.status_code != 200:
            print(f"❌ Ошибка загрузки страницы: {response.status_code}", flush=True)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        news_blocks = soup.select("div.editorialhighlight_medium")

        print(f"🔍 Найдено блоков: {len(news_blocks)}", flush=True)

        for block in news_blocks:
            link_tag = block.find("a", href=True)
            title_tag = block.find("h3")

            if link_tag and title_tag:
                href = link_tag['href']
                title = title_tag.get_text(strip=True)
                full_link = href if href.startswith("http") else f"https://www.fxstreet.ru.com{href}"

                print(f"✅ Найдена новость: {title} → {full_link}", flush=True)
                return {"title": title, "url": full_link}

        print("❗ Новости не найдены", flush=True)
        return None

    except Exception as e:
        print("❌ Ошибка при получении новостей:", e, flush=True)
        return None

# === ОТПРАВКА В TELEGRAM ===
async def send_news():
    global last_sent_link

    news = get_latest_news()
    if not news:
        return

    if news["url"] == last_sent_link:
        print("⏳ Новых новостей нет", flush=True)
        return

    text = f"📰 <b>{news['title']}</b>\n{news['url']}"
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
        print(f"📬 Отправлено в Telegram: {news['title']}", flush=True)
        last_sent_link = news["url"]
    except Exception as e:
        print("❌ Ошибка отправки в Telegram:", e, flush=True)

# === ОСНОВНОЙ ЦИКЛ ===
async def main():
    print("🚀 FXStreet Бот запущен", flush=True)
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="✅ FXStreet бот запущен и следит за новостями.",
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
    except Exception as e:
        print("❌ Ошибка приветствия:", e, flush=True)

    while True:
        await send_news()
        await asyncio.sleep(CHECK_INTERVAL)

# === HTTP-СЕРВЕР ДЛЯ RENDER ===
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"FXStreet Bot is running.")

def run_http_server():
    server = HTTPServer(("0.0.0.0", 10000), DummyHandler)
    print("🌐 HTTP-сервер запущен на порту 10000", flush=True)
    server.serve_forever()

# === ЗАПУСК ===
if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    try:
        asyncio.run(main())
    except Exception as e:
        print("❌ Глобальная ошибка:", e, flush=True)
