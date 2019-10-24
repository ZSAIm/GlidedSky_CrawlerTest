

import simple_spider
import threading
import requests
import time
import traceback
from traceback import print_exc

def get_page_addup(url_format, page):
    req = requests.get(url_format % page, headers=simple_spider.HEADERS)
    text = req.text
    bs4 = simple_spider.BeautifulSoup(text)
    counter = 0
    if int(bs4.find('li', attrs={'class': 'page-item active'}).string) != page:
        raise KeyError('unmatched page number.')
    for i in bs4.find_all('div', attrs={'class': 'col-md-1'}):
        counter += int(i.string.strip())
    PAGE_ADDUP[page - 1] = counter
    PAGE_DATA[page - 1] = text
    print(counter)


def get_addup_wrapper(page):
    try:
        get_page_addup(page_format, page)
    except Exception as e:
        print_exc()
    else:
        return True
    return False


MAX_PAGE = 1000
PAGE_DATA = [None for i in range(1000)]
PAGE_ADDUP = [0 for _ in range(1000)]

page_format = 'http://glidedsky.com/level/web/crawler-basic-2?page=%d'

if __name__ == '__main__':
    for i in range(1000):
        while not get_addup_wrapper(i+1):
            pass
        time.sleep(0.1)

    total = 0
    for i in PAGE_ADDUP:
        total += i
    print(total)