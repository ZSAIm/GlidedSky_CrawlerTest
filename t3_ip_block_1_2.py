import simple_spider
import requests
from threading import Lock
import time


HTTP_PROXIES_COLLECT = [
]

fetch_proxy_lock = Lock()

proxy_api = ''


def get_from_proxy_api(proxy_fetch_api):
    headers = simple_spider.HEADERS.copy()
    while True:
        res = requests.get(proxy_fetch_api, headers=headers, timeout=5)
        if res.status_code != 200:
            time.sleep(0.1)
            continue
        break
    return res.text


def load_ip_proxies(filepath=None, proxies_str=None):
    global HTTP_PROXIES_COLLECT
    if proxies_str is None:
        with open(filepath, 'r') as f:
            proxies_str = f.read()

    for i in proxies_str.split('\n'):
        if i.strip():
            HTTP_PROXIES_COLLECT.append(i.strip())


def get_http_ip_proxy():
    global HTTP_PROXIES_COLLECT
    proxy = None
    with fetch_proxy_lock:
        if HTTP_PROXIES_COLLECT:
            proxy = HTTP_PROXIES_COLLECT.pop(0)
        else:
            load_ip_proxies(proxies_str=get_from_proxy_api(proxy_api))
            if not HTTP_PROXIES_COLLECT:
                time.sleep(5)
            # raise RuntimeError('run out of proxies.')
    if proxy is None:
        return get_http_ip_proxy()
    return {'http': proxy}


def save_proxies():
    global HTTP_PROXIES_COLLECT


class Spider(simple_spider.BasicSpider):
    def get_page_addup(self, page, **kwargs):
        proxy = kwargs.get('proxy')
        if not proxy:
            proxy = get_http_ip_proxy()
        while True:
            try:
                res = requests.get(self.url_page_format % page, headers=simple_spider.HEADERS, proxies=proxy, timeout=10)
            except requests.exceptions.RequestException as e:
                proxy = get_http_ip_proxy()
                continue
            if res.status_code == 200:
                break
            else:
                proxy = get_http_ip_proxy()
            time.sleep(0.1)

        bs4 = simple_spider.BeautifulSoup(res.text, 'lxml')
        if int(bs4.find('li', attrs={'class': 'page-item active'}).string) != page:
            raise KeyError('unmatched page number.')
        counter = 0
        for i in bs4.find_all('div', attrs={'class': 'col-md-1'}):
            counter += int(i.string.strip())

        self.page_number_data[page-1] = counter

    def _spider_handler(self, page, **kwargs):
        if not kwargs.get('proxy', None):
            proxy = get_http_ip_proxy()
            kwargs['proxy'] = proxy
        while not self._addup_wrapper(page, **kwargs):
            pass
        self._queue.put_nowait((page, kwargs))

    def _task_controller(self):
        task_done_counter = 0
        while True:
            page, extra_kw = self._queue.get()
            proxy = extra_kw.get('proxy', None)
            self._queue.task_done()
            task_done_counter += 1

            print(page, task_done_counter)
            if not self.next_page % 100:
                self.save_addup_data("./data/%s.txt" % time.time())
            if task_done_counter + self.start_page - 1 >= self.max_page:
                self.save_addup_data('./data/%s.txt' % time.time())
                print(self.get_total())

                break
            else:
                if self.next_page <= self.max_page:
                    print('NEXT_PAGE: %d' % self.next_page)
                    self._run_next_page({'proxy': proxy})


if __name__ == '__main__':
    url_page_format = 'http://glidedsky.com/level/web/crawler-ip-block-1?page=%d'

    # load_ip_proxies('./proxies/proxies-1')
    spider = Spider(100, url_page_format)
    # spider.get_page_addup(95)
    # spider.load_page_data('./data/1568523298.5229821.txt')
    spider.run()
