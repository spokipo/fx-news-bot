import os
import asyncio
import cloudscraper
from bs4 import BeautifulSoup
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# === Конфигурация из Render Environment ===
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")
MESSAGE_THREAD_ID = int(os.getenv("MESSAGE_THREAD_ID", "0"))
CHECK_INTERVAL = 60  # в секундах

bot = Bot(token=TELEGRAM_BOT_TOKEN)
last_sent_link = None
first_run = True


# === Получение самой свежей новости ===
def get_latest_news():
    print("📡 Получаем страницу новостей...", flush=True)

    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get("https://www.fxstreet.ru.com/news", timeout=10)

        if response.status_code != 200:
            print(f"❌ Ошибка загрузки страницы: {response.status_code}", flush=True)
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Находим первый редакционный блок с заголовком
        block = soup.find("div", class_="editorialhighlight_medium")
        if not block:
            print("❗ Блок editorialhighlight_medium не найден", flush=True)
            return None

        h3 = block.find("h3", class_="fxs_headline_small")
        if not h3:
            print("❗ Заголовок не найден", flush=True)
            return None

        link_tag = h3.find("a", href=True)
        if not link_tag:
            print("❗ Ссылка не найдена", flush=True)
            return None

        title = link_tag.text.strip()
        href = link_tag['href'].strip()

        if not title or not href:
            print("❗ Неполные данные новости", flush=True)
            return None

        full_url = href if href.startswith("http") else f"https://www.fxstreet.ru.com{href}"

        print(f"✅ Найдена новость: {title} → {full_url}", flush=True)
        return {"title": title, "url": full_url}

    except Exception as e:
        print("❌ Ошибка в get_latest_news():", e, flush=True)
        return None


# === Отправка новости в Telegram ===
async def send_news(title, url):
    global last_sent_link

    if url == last_sent_link:
        print("🔁 Новость уже была отправлена", flush=True)
        return

    message = f"📰 <b>{title}</b>\n{url}"

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="HTML",
            message_thread_id=MESSAGE_THREAD_ID
        )
        print("📬 Новость отправлена в Telegram", flush=True)
        last_sent_link = url
    except Exception as e:
        print("❌ Ошибка при отправке:", e, flush=True)


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
            await send_news(news["title"], news["url"])
            if first_run:
                first_run = False
        else:
            print("⏳ Нет новых новостей", flush=True)

        await asyncio.sleep(CHECK_INTERVAL)


# === HTTP-сервер для Render Ping ===
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
