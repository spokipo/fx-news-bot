import os
import asyncio
import cloudscraper
from bs4 import BeautifulSoup
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# === Конфигурация из переменных окружения ===
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")
MESSAGE_THREAD_ID = int(os.getenv("MESSAGE_THREAD_ID", "0"))
CHECK_INTERVAL = 60  # секунд

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# === Глобальное хранилище последней отправленной ссылки ===
last_sent_link = None
first_run = True


# === Получение последней новости ===
def get_latest_news():
    print("📡 Получаем страницу новостей...", flush=True)

    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get("https://www.fxstreet.ru.com/news", timeout=10)

        if response.status_code != 200:
            print(f"❌ Ошибка загрузки страницы: {response.status_code}", flush=True)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        news_blocks = soup.select("div.news-feed__item a[href]")

        print(f"🔍 Найдено новостей: {len(news_blocks)}", flush=True)

        for link_tag in news_blocks:
            title = link_tag.get_text(strip=True)
            href = link_tag['href']

            if not title or not href:
                continue

            if "/news/" not in href:
                continue  # отсекаем лишнее

            full_link = href if href.startswith("http") else f"https://www.fxstreet.ru.com{href}"
            print(f"✅ Свежая новость: {title} → {full_link}", flush=True)

            return {"title": title, "url": full_link}

        print("❗ Не найдено валидных новостей", flush=True)
        return None

    except Exception as e:
        print("❌ Ошибка в get_latest_news():", e, flush=True)
        return None


# === Отправка новости в Telegram ===
async def send_news(title, url):
    global last_sent_link

    if url == last_sent_link:
        print("🔁 Эта новость уже была отправлена", flush=True)
        return

    message = f"📰 <b>{title}</b>\n{url}"
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
        print("📬 Отправлено в Telegram", flush=True)
        last_sent_link = url
    except Exception as e:
        print("❌ Ошибка при отправке в Telegram:", e, flush=True)


# === Основной цикл ===
async def main():
    global first_run

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="✅ Бот запущен и следит за новостями FXStreet",
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
    except Exception as e:
        print("❌ Не удалось отправить стартовое сообщение:", e, flush=True)

    while True:
        news = get_latest_news()

        if news:
            title, url = news["title"], news["url"]
            await send_news(title, url)

            if first_run:
                first_run = False

        else:
            print("⏳ Новостей нет или не удалось получить", flush=True)

        await asyncio.sleep(CHECK_INTERVAL)


# === HTTP-сервер для Render ping ===
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
    print("🌐 HTTP-сервер запущен на порту 10000", flush=True)
    server.serve_forever()


# === Запуск ===
if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    asyncio.run(main())
