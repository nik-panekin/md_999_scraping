import re
import unicodedata

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

# Common text for displaying while script is shutting down
FATAL_ERROR_STR = 'Fatal error. Shutting down.'

# Characters not allowed in filenames
FORBIDDEN_CHAR_RE = r'[<>:"\/\\\|\?\*]'

def fix_filename(filename: str, subst_char: str='_') -> str:
    return re.sub(FORBIDDEN_CHAR_RE, subst_char, filename)

def remove_umlauts(text: str) -> str:
    return (unicodedata.normalize('NFKD', text)
            .encode('ASCII', 'ignore')
            .decode('utf-8'))

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip())

def _get_plain_text(root_tag: Tag) -> str:
    text = ''

    for tag in root_tag.children:
        if isinstance(tag, NavigableString):
            text += re.sub(r'\s+', ' ', str(tag))
        else:
            if tag.name == 'br':
                text += '\n'
            elif tag.name == 'p':
                text += '\n'
                text += _get_plain_text(tag)
                text += '\n'
            elif tag.name in ('ul', 'ol'):
                text += '\n'
                text += _get_plain_text(tag)
            elif tag.name == 'li':
                text += '- ' + _get_plain_text(tag)
                text += '\n'
            else:
                text += _get_plain_text(tag)

    return text

def get_plain_text(root_tag: Tag) -> str:
    plain_text = re.sub(r' +', ' ', _get_plain_text(root_tag).strip())
    return '\n'.join([line.strip() for line in plain_text.split('\n')])

def clean_phone(phone: str) -> str:
    return re.sub(r'\s+|-|\(|\)', '', phone)

def swap_scheme(url: str) -> str:
    if url.startswith('http://'):
        return re.sub(r'^http://', 'https://', url)
    else:
        return re.sub(r'^https://', 'http://', url)

