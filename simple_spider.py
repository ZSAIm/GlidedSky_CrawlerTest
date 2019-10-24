import time
from bs4 import BeautifulSoup
from six.moves.queue import Queue
import requests
from traceback import print_exc
import threading

COOKIE = ''
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
    'Accept': '*/*',
    'Cookie': COOKIE
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
    'Accept': '*/*',
    'Cookie': COOKIE
}


def json_loads_js(expr):
    obj = eval(expr, type('json_loads_js', (dict,), dict(__getitem__=lambda s, n: n))())
    return obj


class BasicSpider:
    def __init__(self, max_task, url_page_format, max_page=1000, start_page=1):
        self.next_page = start_page
        self.start_page = start_page
        self.max_task = max_task
        self.max_page = max_page
        self._queue = Queue()
        self.url_page_format = url_page_format
        self.page_number_data = [None for _ in range(max_page)]

    def _task_controller(self):
        task_done_counter = 0
        while True:
            page, _ = self._queue.get()
            self._queue.task_done()
            if page is not None:
                task_done_counter += 1

            print(page, task_done_counter)
            if task_done_counter % 50 == 0:
                self.save_addup_data('./data/%s-%s.txt' % (__name__, time.time()))
            if task_done_counter + self.start_page - 1 >= self.max_page:
                self.save_addup_data('./data/%s-%s.txt' % (__name__, time.time()))
                print(self.get_total())
                break
            else:
                if self.next_page <= self.max_page:
                    print('NEXT_PAGE: %d' % self.next_page)
                    self._run_next_page()

    def _spider_handler(self, page, **kwargs):
        while not self._addup_wrapper(page, **kwargs):
            pass
        self._queue.put_nowait((page, kwargs))

    def _run_next_page(self, kwargs=None):
        if self.next_page > self.max_page:
            return
        while self.page_number_data[self.next_page-1] is not None:
            self.next_page += 1
            if self.next_page > self.max_page:
                self._queue.put_nowait((None, kwargs or {}))
                return
        threading.Thread(target=self._spider_handler, args=(self.next_page,), kwargs=kwargs).start()
        self.next_page += 1

    def run(self):

        for i in range(self.max_task):
            self._run_next_page()
            time.sleep(0.1)

        ctrl = threading.Thread(target=self._task_controller, name='task_controller')
        ctrl.start()

        # for inspection
        while True:
            time.sleep(1)

    def _addup_wrapper(self, page, **kwargs):
        try:
            self.get_page_addup(page, **kwargs)
        except Exception as e:
            print('===========error')
            print(page)
            print(e)
            # print_exc()
            print('===========error')
        else:
            return True
        return False

    def save_addup_data(self, name):
        tl = [str(i) for i in self.page_number_data]
        with open(name, 'w') as f:
            f.write('\n'.join(tl))

    def get_bs4(self, page):
        req = requests.get(self.url_page_format % page, headers=HEADERS)
        text = req.text
        bs4 = BeautifulSoup(text, 'lxml')
        return bs4

    def get_page_addup(self, page, **kwargs):
        return

    def get_total(self):
        if list(self.check_page_number()):
            raise ValueError('addup data is incomplete ')

        counter = 0
        for i in self.page_number_data:
            counter += i
        return counter

    def check_page_number(self):
        for i, v in enumerate(self.page_number_data):
            if v is None:
                yield i

    def load_page_data(self, filepath):
        self.page_number_data = []
        with open(filepath, 'r') as f:
            data_str = f.read()
        for i in data_str.split('\n'):
            if i:
                if i.strip() == 'None' or i.strip() == '0':
                    self.page_number_data.append(None)
                else:
                    self.page_number_data.append(int(i.strip()))
