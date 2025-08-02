import cloudscraper
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
CHECK_INTERVAL = 60  # Интервал проверки новостей (секунды)

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# === ГЛОБАЛЬНАЯ ПАМЯТЬ ===
last_link = None
first_run = True

# === ПАРСИНГ НОВОСТЕЙ ===
def get_news():
    url = "https://www.fxstreet.ru.com/news"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, headers=headers, timeout=10)

        print("📥 Ответ сервера:", resp.status_code)
        if "Just a moment" in resp.text:
            print("❌ Cloudflare всё ещё блокирует!")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # 👉 Используем более общий селектор
        all_links = soup.find_all("a", href=True)
        news = []

        for el in all_links:
            title = el.get_text(strip=True)
            href = el["href"]

            # Пропускаем мусорные ссылки
            if not href.startswith("/news/"):
                continue

            link = "https://www.fxstreet.ru.com" + href
            news.append((title, link))

        print("💬 Ссылок найдено:", len(news))
        for t, l in news:
            print("🔗", t, "=>", l)

        return news

    except Exception as e:
        print("Ошибка при получении новостей:", e)
        return []
    except Exception as e:
        print("Ошибка при получении новостей:", e)
        return []

# === ОТПРАВКА НОВОСТЕЙ ===
async def send_news(news_list):
    global last_link, first_run

    news_list = list(reversed(news_list))  # От старых к новым

    for title, link in news_list:
        if link == last_link:
            continue  # Уже отправляли

        msg = f"📰 <b>{title}</b>\n{link}"
        print("Отправляем:", title)

        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode="HTML",
                message_thread_id=MESSAGE_THREAD_ID
            )
            last_link = link
            await asyncio.sleep(1)
        except Exception as e:
            print("Ошибка отправки:", e)

        if first_run:
            break  # Только одну новость при старте

    first_run = False

# === ОСНОВНОЙ ЦИКЛ ===
async def main():
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
            print(f"🔄 Найдено новостей: {len(news)}")
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
