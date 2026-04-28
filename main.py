import requests
from bs4 import BeautifulSoup
import csv
import logging
import os

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parser.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

URL = "https://xn----etbpba5admdlad.xn--p1ai/%D0%BA%D1%83%D0%BF%D0%B8%D1%82%D1%8C-%D0%BA%D0%BE%D0%BC%D0%BC%D0%B5%D1%80%D1%87%D0%B5%D1%81%D0%BA%D1%83%D1%8E-%D0%BD%D0%B5%D0%B4%D0%B2%D0%B8%D0%B6%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D1%8C-%D0%B2-%D0%BC%D0%BE%D1%81%D0%BA%D0%B2%D0%B5-%D1%81-%D1%82%D0%BE%D1%80%D0%B3%D0%BE%D0%B2"
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "User-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
}
CSV_PATH = "My_project/data/all_lots.csv"


def get_html(url: str) -> str | None:
    """Получает HTML код страницы.

    Args:
        url: Ссылка на страницу.

    Returns:
        Исходной HTML-код страницы.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети при запросе к {url}: {e}")
        return None


def parse_listing(html: str) -> tuple[dict[str, str], str | None]:
    """Собирает ссылки на лоты со списка.

    Args:
        html: Исходной HTML-код страницы.

    Returns:
        Кортеж, содержащий:
            dict: Словарь, где ключи — названия лотов, а значения — их URL.
            str: | None: URL следующей страницы или None, если ее нет.
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        links = {}
        items = soup.find_all(class_="card__title")
        for item in items:
            a_tag = item.find("a")
            if a_tag:
                links[a_tag.get_text(strip=True)] = a_tag.get("href")

        next_page = soup.find("a", rel="next")
        next_url = next_page.get("href") if next_page else None

        return links, next_url

    except Exception as e:
        logger.error(f"Ошибка при парсинге списка: {e}")
        return {}, None


def extract_detail_data(html: str, url: str) -> dict:
    """Парсит страницу конкретного лота.

    Args:
        html: Исходной HTML-код страницы лота.
        url: Ссылка на лот (для сохранения в итоговый словарь).

    Returns:
        Словарь с данными о лоте.
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        data = {
            "Название лота": "Н/Д",
            "Цена (текущая)": "Н/Д",
            "Тип аукциона": "Н/Д",
            "Регион": "Н/Д",
            "Начало ценовых предложений": "Н/Д",
            "Начало приема заявок": "Н/Д",
            "Конец приема заявок": "Н/Д",
            "Ссылка": "Н/Д",
        }
        container = soup.find(class_="lot-card__data")
        if container:
            rows = container.find_all("li")
            for row in rows:
                text = row.get_text()
                if "Регион:" in text:
                    data["Регион"] = text.replace("Регион:", "").strip()
                if "Начало приема ценовых предложений:" in text:
                    data["Начало ценовых предложений"] = text.replace(
                        "Начало приема ценовых предложений:", ""
                    ).strip()
                if "Начало приёма заявок:" in text:
                    data["Начало приема заявок"] = text.replace(
                        "Начало приёма заявок:", ""
                    ).strip()
                if "Конец приёма заявок:" in text:
                    data["Конец приема заявок"] = text.replace(
                        "Конец приёма заявок:", ""
                    ).strip()

        lot_price_and_type_auction = soup.find(class_="lot-card__bids")
        if lot_price_and_type_auction:
            data["Цена (текущая)"] = lot_price_and_type_auction.get("data-current-bid")
            data["Тип аукциона"] = lot_price_and_type_auction.get("data-ico-tooltip")

        return data

    except Exception as e:
        logger.warning(f"Не удалось полностью спарсить детали по ссылке {url}: {e}")
        return {"Ссылка": url}


def save_row_to_csv(data: dict, fieldnames: list) -> None:
    """Добавляет строку с данными в CSV-файл.
    Args:
       data: Словарь с данными о лоте.
       fieldnames: Список заголовков (названия столбцов).
    """
    try:
        # Проверяем наличие папки
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        with open(CSV_PATH, "a", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow(data)
    except IOError as e:
        logger.error(f"Ошибка записи в CSV: {e}")


def main():
    current_url = URL
    all_results = []
    logger.info("Шаг 1: Запуск парсера...")
    while current_url:
        html = get_html(current_url)
        if not html:
            break

        links, next_url = parse_listing(html)
        for name, href in links.items():
            all_results.append({"name": name, "url": href})

        current_url = next_url

    logger.info(f"Найдено ссылок: {len(all_results)}")
    logger.info("Шаг 2: Собираем данные по каждой лоте...")
    fieldnames = [
        "Название лота",
        "Цена (текущая)",
        "Тип аукциона",
        "Регион",
        "Начало ценовых предложений",
        "Начало приема заявок",
        "Конец приема заявок",
        "Ссылка",
    ]

    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

    for item in all_results:
        detail_html = get_html(item["url"])
        if detail_html:
            details = extract_detail_data(detail_html, item["url"])
            details["Название лота"] = item["name"]
            details["Ссылка"] = item["url"]
            save_row_to_csv(details, fieldnames)


if __name__ == "__main__":
    main()
