import asyncio
import cloudscraper
from bs4 import BeautifulSoup
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = "8374044886:AAHaI_LNKeW90A5sOYA_uzs5nfxVWBoM2us"
TELEGRAM_CHAT_ID = "-1002518445518"
MESSAGE_THREAD_ID = 15998
CHECK_INTERVAL = 60  # интервал проверки (в секундах)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
last_sent_link = None

# === ПОЛУЧЕНИЕ НОВОСТЕЙ ===
def get_latest_news():
    print("📡 Получаем страницу новостей...", flush=True)

    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get("https://www.fxstreet.ru.com/news", timeout=10)

        if "Just a moment" in response.text or "Enable JavaScript" in response.text:
            print("⚠️ Cloudflare всё ещё блокирует", flush=True)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        news_items = soup.select("div.news-feed__item a")

        print(f"🔎 Найдено элементов: {len(news_items)}", flush=True)

        for el in news_items:
            href = el.get("href")
            title = el.get_text(strip=True)

            if not href or not title:
                continue

            full_url = "https://www.fxstreet.ru.com" + href
            print(f"✅ Новость: {title} → {full_url}", flush=True)
            return title, full_url  # возвращаем первую новость

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

    title, link = news

    if link == last_sent_link:
        print("⏳ Новых новостей нет", flush=True)
        return

    message = f"📰 <b>{title}</b>\n{link}"
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
        print(f"✅ Отправлено в Telegram: {title}", flush=True)
        last_sent_link = link
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
        print("❌ Ошибка при отправке приветствия:", e, flush=True)

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
