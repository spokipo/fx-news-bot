import cloudscraper
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = "8374044886:AAHaI_LNKeW90A5sOYA_uzs5nfxVWBoM2us"
TELEGRAM_CHAT_ID = "-1002518445518"
CHECK_INTERVAL = 60  # интервал (пока не используется)

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# === ПАРСИНГ НОВОСТЕЙ ===
def get_news():
    print("📡 Вызов get_news()")

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

            full_link = "https://www.fxstreet.ru.com" + href
            news.append((title, full_link))

        print(f"💬 Найдено новостей: {len(news)}")
        for t, l in news:
            print("🔗", t, "=>", l)

        return news

    except Exception as e:
        print("❌ Ошибка при получении новостей:", e)
        return []

# === ОСНОВНОЙ ЦИКЛ (отладочный) ===
async def main():
    print("✅ main() запущен")

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="✅ FXStreet Бот стартует отладку",
            parse_mode="HTML"
        )
    except Exception as e:
        print("❌ Ошибка при запуске:", e)

    print("📡 Вызываем get_news()...")
    news = get_news()
    print("📦 Получено:", len(news), "новостей")

    for title, link in news:
        print("🔗", title, "=>", link)

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f"🧪 Найдено <b>{len(news)}</b> новостей.",
            parse_mode="HTML"
        )
    except Exception as e:
        print("❌ Ошибка при отправке результата:", e)

    await asyncio.sleep(3600)  # оставим процесс живым

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
    print("🌐 HTTP-сервер запущен")
    server.serve_forever()

# === ЗАПУСК ===
if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    try:
        asyncio.run(main())
    except Exception as e:
        print("❌ Глобальная ошибка:", e)