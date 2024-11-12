import csv
import json
import os.path
import logging

NL = '\r\n'
LT = '\r\n'
CSV_DELIMITER = ','

LAST_PROCESSED_PAGE_FILENAME = 'last_processed_page.txt'

# Saves last processed page
def save_last_page(page: int) -> bool:
    try:
        with open(LAST_PROCESSED_PAGE_FILENAME, 'w') as f:
            f.write(str(page))
    except OSError:
        logging.exception("Can't save last processed page to a file.")
        return False
    return True

# Loads previously saved last processed page
def load_last_page() -> int:
    page = 0
    if os.path.exists(LAST_PROCESSED_PAGE_FILENAME):
        try:
            with open(LAST_PROCESSED_PAGE_FILENAME, 'r') as f:
                page = int(f.read())
        except OSError:
            logging.warning("Can't load last processed page from file.")
        except ValueError:
            logging.exception(f'File {LAST_PROCESSED_PAGE_FILENAME} '
                              'is currupted.')
    return page

# Saving prepared item data to a CSV file
def save_item_csv(item: dict, columns: list, filename: str,
                  first_item=False) -> bool:
    try:
        with open(filename, 'w' if first_item else 'a',
                  newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=CSV_DELIMITER, lineterminator=LT)
            if first_item:
                writer.writerow(columns)
            writer.writerow([item.get(key, '') for key in columns])
    except OSError:
        logging.exception(f"Can't write to CSV file {filename}.")
        return False
    except Exception as e:
        logging.exception('Scraped data saving fault.')
        return False

    return True

# Saves prepared items list to a CSV file
def save_items_csv(items: list, columns: list, filename: str) -> bool:
    for index, item in enumerate(items):
        if not save_item_csv(item, columns, filename,
                             first_item = (index == 0)):
            return False

    return True

def load_items_csv(filename: str, columns: list) -> list:
    if not os.path.exists(filename):
        return []

    items = []

    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=CSV_DELIMITER, lineterminator=LT)
            next(reader)
            for row in reader:
                item = {}
                for index, key in enumerate(columns):
                    item[key] = row[index]
                items.append(item)
    except OSError:
        logging.exception(f"Can't read CSV file {filename}.")
    except Exception:
        logging.exception('CVS file reading fault.')

    return items

# Saves item list to a JSON file
def save_items_json(items: list, filename: str) -> bool:
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=4)
    except OSError:
        logging.exception(f"Can't write to the file {filename}.")
        return False

    return True

def load_items_json(filename: str) -> list:
    try:
        with open(filename, encoding='utf-8') as f:
            items = json.load(f)
    except OSError:
        logging.warning(f"Can't load the file {filename}.")
        return []

    return items
