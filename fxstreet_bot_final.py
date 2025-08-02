import cloudscraper
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = "8374044886:AAHaI_LNKeW90A5sOYA_uzs5nfxVWBoM2us"
TELEGRAM_CHAT_ID = "-1002518445518"
MESSAGE_THREAD_ID = 15998
CHECK_INTERVAL = 60  # интервал проверки (в секундах)

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# === ГЛОБАЛЬНАЯ ПАМЯТЬ ===
last_link = None
first_run = True

# === ПОЛУЧЕНИЕ НОВОСТЕЙ ===
def get_news():
    url = "https://www.fxstreet.ru.com/news"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, headers=headers, timeout=10)

        print("📥 Ответ сервера:", resp.status_code)

        if "Just a moment" in resp.text or "Enable JavaScript" in resp.text:
            print("❌ Cloudflare всё ещё блокирует!")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        all_links = soup.find_all("a", href=True)

        news = []
        for el in all_links:
            href = el["href"]
            title = el.get_text(strip=True)

            if not href.startswith("/news/"):
                continue

            link = "https://www.fxstreet.ru.com" + href
            news.append((title, link))

        print(f"💬 Найдено новостей: {len(news)}")
        for title, link in news:
            print("🔗", title, "=>", link)

        return news

    except Exception as e:
        print("Ошибка при получении новостей:", e)
        return []

# === ОТПРАВКА НОВОСТЕЙ ===
async def send_news(news_list):
    global last_link, first_run

    news_list = list(reversed(news_list))  # от старых к новым

    for title, link in news_list:
        if link == last_link:
            continue  # уже отправлено

        msg = f"📰 <b>{title}</b>\n{link}"
        print("📤 Отправка новости:", title)

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
            break  # при первом запуске — только одну

    first_run = False

# === ОСНОВНОЙ ЦИКЛ ===
async def main():
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="✅ FXStreet Бот запущен и следит за новостями.",
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
            print("Ошибка в основном цикле:", e)
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
    print("🌐 HTTP-сервер запущен на порту 10000")
    server.serve_forever()

# === ЗАПУСК ===
if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    asyncio.run(main())
