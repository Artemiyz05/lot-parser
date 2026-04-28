from main import parse_listing, extract_detail_data


def test_extract_detail_data() -> None:
    """
    Тестирует корректность извлечения данных из HTML-структуры карточки лота.
    Проверяет парсинг региона, дат и аукционных данных.
    """
    fake_detail_html = """
    <div class="lot-card__data">
        <ul>
            <li>Регион: Санкт-Петербург</li>
            <li>Начало приёма заявок: 01.01.2026</li>
        </ul>
    </div>
    <div class="lot-card__bids" data-current-bid="500000" data-ico-tooltip="Аукцион"></div>
    """
    url: str = "http://test-lot.com/1"

    # Act (Действие)
    result: dict = extract_detail_data(fake_detail_html, url)

    # Assert (Проверка результата)
    assert result["Регион"] == "Санкт-Петербург"
    assert result["Начало приема заявок"] == "01.01.2026"
    assert result["Цена (текущая)"] == "500000"
    assert result["Тип аукциона"] == "Аукцион"


def test_parse_listing_valid_html() -> None:
    """
    Тестирует парсинг страницы списка лотов.

    Проверяет способность функции корректно собирать названия лотов,
    их ссылки и определять URL следующей страницы пагинации.
    """
    fake_html: str = """
    <div class="card__title"><a href="http://link1.com">Лот 1</a></div>
    <a rel="next" href="http://nextpage.com">Далее</a>
    """
    links, next_url = parse_listing(fake_html)

    assert len(links) == 1
    assert links["Лот 1"] == "http://link1.com"
    assert next_url == "http://nextpage.com"


def test_parse_listing_empty_html() -> None:
    """
    Тестирует поведение парсера при получении пустого или некорректного HTML.

    Убеждается, что функция не падает с ошибкой, а возвращает пустой словарь
    и None для следующей страницы.
    """
    links, next_url = parse_listing("")
    assert links == {}
    assert next_url is None
