

import simple_spider
import requests
import time
from traceback import print_exc
from fontTools.ttLib import TTFont
import re
import threading
from six.moves.queue import Queue
from nbdler import Request, dlopen


def handle_font_remap(bs4):
    font_style_text = None
    for i in bs4.find_all('style'):
        if 'font-face' in i.string:
            font_style_text = i.string
            break

    if font_style_text is None:
        raise ValueError('cannot find font-face.')

    rex_url = re.compile('url\("(.*?)"\)', re.I)
    font_url = rex_url.search(font_style_text).group(1)

    name = './fonts/%s.woff' % time.perf_counter_ns()
    req = Request(url=font_url, headers=simple_spider.HEADERS, filepath=name)
    dl = dlopen(req)
    dl.start()
    dl.trap()
    dl.close()

    remap_key = parse_font(name)

    return remap_key


# cid00017 -> # cid00026: 0->9
def parse_font(font_file):
    font = TTFont(font_file)
    cmap = font['cmap'].getBestCmap()
    counter = 0
    # key: origin
    # value: new
    number_remap = {}
    for k, v in sorted(cmap.items(), key=lambda k: k[0]):
        new_number = int(v[3:]) - 17
        origin_numbder = counter
        counter += 1
        number_remap[origin_numbder] = new_number

    return number_remap


def parse_font_number(origin_txt, numbder_remap):
    origin_array = []

    for v in origin_txt:
        origin_array.append(str(numbder_remap[int(v)]))

    return int(''.join(origin_array))


def get_page_addup(url_format, page):
    req = requests.get(url_format % page, headers=simple_spider.HEADERS)
    text = req.text
    bs4 = simple_spider.BeautifulSoup(text)

    remap_num = handle_font_remap(bs4)

    counter = 0
    for i in bs4.find_all('div', attrs={'class': 'col-md-1'}):
        counter += parse_font_number(i.string.strip(), remap_num)
    PAGE_ADDUP[page - 1] = counter
    thread_queue.put_nowait(page)


def get_addup_wrapper(page):
    try:
        get_page_addup(page_format, page)
    except Exception as e:
        print('===========error')
        print(page)
        print_exc()
        print('===========error')
    else:
        return True
    return False


def spider_handler(page):
    while not get_addup_wrapper(page):
        pass


def thread_handle():
    global NEXT_PAGE

    task_done_counter = 0
    while True:
        data = thread_queue.get()
        thread_queue.task_done()

        task_done_counter += 1

        print(data, task_done_counter)
        if task_done_counter >= MAX_PAGE:
            cal_addup()
            break
        else:
            if NEXT_PAGE <= MAX_PAGE:

                print('NEXT_PAGE: %d' % NEXT_PAGE)
                threading.Thread(target=spider_handler, args=(NEXT_PAGE,)).start()
                NEXT_PAGE += 1


def cal_addup():
    global PAGE_ADDUP
    total = 0
    for i in PAGE_ADDUP:
        total += i
    print(total)


MAX_PAGE = 1000
PAGE_ADDUP = [0 for _ in range(1000)]
NEXT_PAGE = 1
MAX_TASK = 1
thread_queue = Queue()

page_format = 'http://glidedsky.com/level/web/crawler-font-puzzle-1?page=%d'


if __name__ == '__main__':


    for i in range(MAX_TASK):
        threading.Thread(target=spider_handler, args=(NEXT_PAGE,)).start()
        NEXT_PAGE += 1
        time.sleep(2)

    ctrler = threading.Thread(target=thread_handle, name='thread-queue')
    ctrler.start()

    while True:
        time.sleep(1)

    ctrler.join()
    cal_addup()
    exit()