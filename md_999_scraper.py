import re
import os
import sys
import logging

from bs4 import BeautifulSoup

from scraping_utils.setup_logging import setup_logging
from scraping_utils.http_request import HttpRequest
from scraping_utils.misc import FATAL_ERROR_STR, clean_text, get_plain_text
from scraping_utils.save_load import save_items_json, load_items_json
from scraping_utils.save_load import save_items_csv

CSV_FILENAME = 'items.csv'
JSON_FILENAME = 'items.json'

HTTP_HOST = 'https://999.md'
CATEGORY_URL = HTTP_HOST + '/ru/list/computers-and-office-equipment/processors'

############################### Global Objects ################################
request = HttpRequest()
###############################################################################


def get_page_count(url: str) -> int:
    html = request.get_html(url)
    if not html:
        return None

    try:
        bs = BeautifulSoup(html, 'lxml')
        # page_count = int(
        #     bs.find('li', {'class': 'is-last-page'})
        #     .a.attrs['href'].split('?page=')[-1]
        # )
        page_count = int(
            bs.find('nav', {'class': 'paginator'}).ul.find_all('li')[-1]
            .a.attrs['href'].split('?page=')[-1])
    except (AttributeError, ValueError, KeyError, TypeError):
        logging.exception('Error while parsing page count.')
        return None

    return page_count


def get_item_links(url: str) -> list:
    html = request.get_html(url)
    if not html:
        return None

    links = []

    try:
        bs = BeautifulSoup(html, 'lxml')
        items = (bs.find('ul', {'class': 'ads-list-photo large-photo'})
                .find_all('li', {'class': 'ads-list-photo-item'}))

        for item in items:
            # Skip advertisements
            if item.find('span', {'class': 'advertising-label'}) == None:
                item_link = item.find('div',
                    {'class': 'ads-list-photo-item-title'}).a.attrs['href']
                item_url = HTTP_HOST + item_link

                # Handling redirect
                if item_link.startswith('/booster/link?token='):
                    item_url = request.get(item_url).url
                    if not item_url:
                        return None

                # Forced changing locale to russian
                links.append(item_url.replace('/ro/', '/ru/'))
    except (AttributeError, ValueError, KeyError, TypeError):
        logging.exception('Error while parsing item links.')
        return None

    return links


def item_is_scraped(items: list, link: str) -> bool:
    for item in items:
        if item['Ссылка'] == link:
            logging.info(f'The item "{link}" is already scraped. Skipping.')
            return True
    return False


def scrape_item(url: str) -> dict:
    html = request.get_html(url)
    if not html:
        return None

    item = {
        'Заголовок': '',
        'Описание': '',
        'Производитель': '',
        'Тип': '',
        'Тип разъема': '',
        'Количество ядер': '',
        'Ссылка': url,
        'Дата обновления': '',
        'Просмотры': '',
        'Цена': '',
        'Регион': '',
        'Контакты': '',
    }

    bs = BeautifulSoup(html, 'lxml')

    try:
        item['Заголовок'] = clean_text(
            bs.find('h1', {'itemprop': 'name'}).get_text())
    except AttributeError:
        logging.exception('Error while parsing "Заголовок".')

    try:
        description = bs.find('div', {'itemprop': 'description'})
        if description:
            item['Описание'] = description.get_text().strip()
    except AttributeError:
        logging.exception('Error while parsing "Описание".')

    try:
        producer_span = bs.find(
            'span', {'class': 'adPage__content__features__key',
                     'itemprop': 'name'},
            string=re.compile('Производитель')
        )
        if producer_span:
            item['Производитель'] = clean_text(
                producer_span.find_next_sibling('span').a.get_text())
    except AttributeError:
        logging.exception('Error while parsing "Производитель".')

    try:
        type_span = bs.find(
            'span', {'class': 'adPage__content__features__key',
                     'itemprop': 'name'},
            string=re.compile(r'^\s*Тип\s*$')
        )
        if type_span:
            item['Тип'] = clean_text(
                type_span.find_next_sibling('span').get_text())
    except AttributeError:
        logging.exception('Error while parsing "Тип".')

    try:
        socket_span = bs.find(
            'span', {'class': 'adPage__content__features__key',
                     'itemprop': 'name'},
            string=re.compile('Тип разъема')
        )
        if socket_span:
            item['Тип разъема'] = clean_text(
                socket_span.find_next_sibling('span').get_text())
    except AttributeError:
        logging.exception('Error while parsing "Тип разъема".')

    try:
        cores_span = bs.find(
            'span', {'class': 'adPage__content__features__key',
                     'itemprop': 'name'},
            string=re.compile('Количество ядер')
        )
        if cores_span:
            item['Количество ядер'] = clean_text(
                cores_span.find_next_sibling('span').get_text())
    except AttributeError:
        logging.exception('Error while parsing "Количество ядер".')

    try:
        updated = (bs.find('div', {'class': 'adPage__aside__stats'})
                     .find('div', {'class': 'adPage__aside__stats__date'}))
        if updated:
            item['Дата обновления'] = (
                updated.get_text().split('Дата обновления:')[1].strip())
    except (AttributeError, KeyError, IndexError):
        logging.exception('Error while parsing "Дата обновления".')

    try:
        views = (bs.find('div', {'class': 'adPage__aside__stats'})
                   .find('div', {'class': 'adPage__aside__stats__views'}))
        if views:
            item['Просмотры'] = (
                views.span.get_text().split('Просмотры:')[1].strip())
    except (AttributeError, KeyError, IndexError):
        logging.exception('Error while parsing "Просмотры".')

    try:
        price = (bs.find('div', {'class': 'adPage__content__footer__wrapper'})
                   .find('li', {'class':
            'adPage__content__price-feature__prices__price'}))

        if price:
            item['Цена'] = clean_text(price.get_text())
    except AttributeError:
        logging.exception('Error while parsing "Цена".')

    try:
        region = bs.find('dl', {'class': 'adPage__content__region grid_18'})
        if region:
            item['Регион'] = region.get_text().split('Регион:')[1]
            item['Регион'] = ', '.join(
                [part.strip() for part in item['Регион'].split(',')])
    except (AttributeError, KeyError, IndexError):
        logging.exception('Error while parsing "Регион".')

    try:
        tel = (bs.find('div', {'class': 'adPage__content__footer__wrapper'})
                 .find('a', href=re.compile(r'^tel:')))
        if tel:
            item['Контакты'] = tel.attrs['href'].split('tel:')[1]
    except (AttributeError, KeyError, IndexError):
        logging.exception('Error while parsing "Контакты".')

    return item


def scrape_all_items():
    if os.path.exists(JSON_FILENAME):
        logging.info('Loading previous scraping result.')
        items = load_items_json(JSON_FILENAME)
    else:
        items = []

    page_count = get_page_count(CATEGORY_URL)
    if page_count == None:
        return None
    logging.info(f'Total page count: {page_count}.')

    for page in range(1, page_count + 1):
        logging.info(f'Scraping items for page {page} of {page_count}.')

        item_links = get_item_links(f'{CATEGORY_URL}?page={page}')
        if item_links == None:
            return None

        for item_link in item_links:
            if item_is_scraped(items, item_link):
                continue
            logging.info(f'Scraping item "{item_link}".')
            item = scrape_item(item_link)
            if item != None:
                items.append(item)

        if save_items_json(items, JSON_FILENAME):
            result = 'OK'
        else:
            result = 'FAILURE'

        logging.info('Saving intermediate results '
                     + f'for page {page}: {result}.')

    return items


def main():
    setup_logging()

    logging.info('Starting scraping process.')

    if '--restart' in sys.argv:
        try:
            os.remove(JSON_FILENAME)
        except FileNotFoundError:
            # Файл не существует — просто пропускаем без сообщений
            pass
        except OSError as e:
            # Обработка других ошибок уровня ОС, таких как отсутствие прав
            print(f'Error while removing file "{JSON_FILENAME}": {e}')

    # item = scrape_item('https://999.md/ru/86500605')
    # print(item)
    # exit()

    items = scrape_all_items()
    if items == None:
        logging.error(FATAL_ERROR_STR)
        return

    logging.info('Scraping process complete. Now saving the results.')
    if not save_items_csv(items, list(items[0].keys()), CSV_FILENAME):
        logging.error(FATAL_ERROR_STR)
        return

    logging.info('Saving complete.')


if __name__ == '__main__':
    main()
