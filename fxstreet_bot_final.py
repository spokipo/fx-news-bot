import requests
from bs4 import BeautifulSoup
import time
import asyncio
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = "8374044886:AAHaI_LNKeW90A5sOYA_uzs5nfxVWBoM2us"
TELEGRAM_CHAT_ID = "-1002518445518"
MESSAGE_THREAD_ID = 15998
CHECK_INTERVAL = 60  # интервал проверки в секундах

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# === ГЛОБАЛЬНАЯ ПАМЯТЬ ПОСЛЕДНЕЙ ССЫЛКИ ===
last_link = None

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

            if title and link:
                news.append((title, link))

        return news

    except Exception as e:
        print("Ошибка при получении новостей:", e)
        return []

# === ОТПРАВКА НОВОСТЕЙ ===
async def send_news(news_list):
    global last_link
    for title, link in news_list:
        if link == last_link:
            break  # Остальные уже были отправлены

        msg = f"📰 <b>{title}</b>\n{link}"
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode="HTML",
                message_thread_id=MESSAGE_THREAD_ID
            )
            if not last_link:
                last_link = link  # сохраняем только первую ссылку (сверху страницы)
            await asyncio.sleep(1)
        except Exception as e:
            print("Ошибка отправки:", e)

# === ОСНОВНОЙ ЦИКЛ ===
async def main():
    global last_link

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="✅ Бот запущен и следит за новостями FXStreet",
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
            print("Ошибка в цикле:", e)
            await asyncio.sleep(30)

# === HTTP-СЕРВЕР ДЛЯ RENDER ===
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
