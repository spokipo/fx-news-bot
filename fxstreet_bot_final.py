
import requests
from bs4 import BeautifulSoup
import time
import telegram

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = "8374044886:AAHaI_LNKeW90A5sOYA_uzs5nfxVWBoM2us"
TELEGRAM_CHAT_ID = "-2518445518"
MESSAGE_THREAD_ID = 15998
CHECK_INTERVAL = 60  # в секундах

# === ИНИЦИАЛИЗАЦИЯ ===
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
posted_links = set()

def get_news():
    url = "https://www.fxstreet.com/ru/news"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    news_items = soup.select("div.news-feed__item")
    news = []

    for item in news_items:
        title_tag = item.select_one("a.news-feed__item__title")
        if title_tag:
            title = title_tag.text.strip()
            link = "https://www.fxstreet.com" + title_tag.get("href")
            if link not in posted_links:
                news.append((title, link))
    return news

def send_news(news_list):
    for title, link in news_list:
        message = f"📰 <b>{title}</b>\n{link}"
        try:
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode=telegram.ParseMode.HTML,
                message_thread_id=MESSAGE_THREAD_ID
            )
            posted_links.add(link)
        except Exception as e:
            print(f"Ошибка при отправке: {e}")

def main():
    while True:
        try:
            news = get_news()
            if news:
                send_news(news)
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            time.sleep(30)

 # Запуск фейкового веб-сервера в отдельном потоке
    threading.Thread(target=run_http_server).start()


if __name__ == "__main__":
    main()
