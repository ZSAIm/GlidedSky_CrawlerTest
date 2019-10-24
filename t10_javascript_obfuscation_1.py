
import simple_spider
import hashlib
import requests
import json

number_data_url = 'http://glidedsky.com/api/level/web/crawler-javascript-obfuscation-1/items'
number_data_params_template = {
    'page': None,
    't': None,
    'sign': None
}


class Spider(simple_spider.BasicSpider):
    def get_page_addup(self, page, **kwargs):
        sess = requests.Session()
        headers = simple_spider.HEADERS.copy()

        cookie_dict = {}
        for i in headers['Cookie'].split(';'):
            k, v = i.split('=')
            cookie_dict[k.strip()] = v.strip()
        # cookies =
        del headers['Cookie']
        sess.cookies = requests.utils.cookiejar_from_dict(cookie_dict)
        sess.headers = headers
        res = sess.get(self.url_page_format % page)

        bs4 = simple_spider.BeautifulSoup(res.text, 'lxml')
        if int(bs4.find('li', attrs={'class': 'page-item active'}).string) != page:
            raise KeyError('unmatched page number.')
        t_tag = None
        for tag in bs4.find_all('div', attrs={'class': 'container'}):
            if tag.has_attr('p'):
                t_tag = tag
                break
        if not t_tag:
            raise ValueError()
        t = str(int((int(t_tag.get('t')) - 99) / 99))

        params = number_data_params_template.copy()
        params['t'] = t
        params['page'] = page
        params['sign'] = hashlib.sha1(('Xr0Z-javascript-obfuscation-1' + t).encode('utf-8')).hexdigest()

        res = sess.get(number_data_url, params=params)

        res_json = json.loads(res.text)
        counter = 0
        if not res_json:
            raise ValueError()
        for i in res_json['items']:
            counter += i
        self.page_number_data[page - 1] = counter


if __name__ == '__main__':
    url_page_format = 'http://glidedsky.com/level/web/crawler-javascript-obfuscation-1?page=%d'

    spider = Spider(35, url_page_format)
    spider.run()



