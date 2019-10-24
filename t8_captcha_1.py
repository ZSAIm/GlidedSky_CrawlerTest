import simple_spider
import base64
import requests
import json
import random
import time
import re
from PIL import Image
from io import BytesIO

SUBSID_PREHANDLE = 1
SUBSID_FRAME = 2
SUBSID_BG = 3
SUBSID_SLIDE = 4

IMG_INDEX_BG = 1
IMG_INDEX_SLIDE = 2

THRESHOLD = 220
BORDER_FACTOR = 0.30
INNER_FACTOR = 0.65

from collections import namedtuple

# =====================================================
#                width * height     offset_x   offset_y
# slide size =     136 * 136            23         23
# bg    size =     680 * 390             0          0
# =====================================================


ImageInfo = namedtuple('ImageInfo', 'width height x_start x_end y_start y_end')

SLIDE_SIZE = ImageInfo(136, 136, 23, 136 - 24, 23, 136 - 24)
BG_SIZE = ImageInfo(680, 390, 0, 0, 0, 0)


def load_raw_img(fp):
    img = Image.open(fp)
    pixels = img.load()

    return img, pixels


def img_threshold(fp, name=None, threshold=THRESHOLD):
    img = Image.open(fp)
    limg = img.convert('L')
    pixels = limg.load()

    for y in range(limg.height):
        for x in range(limg.width):
            pixels[x, y] = 0 if pixels[x, y] < threshold else 255
    if name:
        limg.save(name)
    return limg, pixels


def scan_column_white_number(pixels, x, y_start, y_end):
    white_counter = 0
    for y in range(y_start, y_end):
        if pixels[x, y] >= 150:
            white_counter += 1
    return white_counter


def scan_row_white_number(pixels, y, x_start, x_end):
    white_counter = 0
    for x in range(x_start, x_end):
        if pixels[x, y] >= 150:
            white_counter += 1
    return white_counter


def scan_inner_black_number(pixels, x_start, x_end, y_start, y_end):
    black_counter = 0
    for y in range(y_start, y_end + 1):
        for x in range(x_start, x_end + 1):
            if pixels[x, y] == 0:
                black_counter += 1

    return black_counter


def scan_gap_position(imgsrc, pixels, top):
    def check_column_white_scale(x, factor=BORDER_FACTOR):
        """ Return True if half of pixels on the column are white. """

        white_cnt = scan_column_white_number(
            pixels, x,
            top,
            top + SLIDE_SIZE.y_end - SLIDE_SIZE.y_start
        )

        if white_cnt < (SLIDE_SIZE.y_end - SLIDE_SIZE.y_start) * factor:
            return False
        return True

    def check_row_white_scale(x_start, y, factor=BORDER_FACTOR):
        white_cnt = scan_row_white_number(
            pixels, y,
            x_start,
            x_start + SLIDE_SIZE.x_end - SLIDE_SIZE.x_start
        )

        if white_cnt < (SLIDE_SIZE.y_end - SLIDE_SIZE.y_start) * factor:
            return False
        return True

    def check_inner_black_scale(x, factor=INNER_FACTOR):
        black_cnt = scan_inner_black_number(
            pixels, x + 1, x + SLIDE_SIZE.x_end - SLIDE_SIZE.x_start - 1,
                    top + 1,
                    top + SLIDE_SIZE.y_end - SLIDE_SIZE.y_start - 1
        )

        if black_cnt < (SLIDE_SIZE.x_end - SLIDE_SIZE.x_start - 2) * \
                (SLIDE_SIZE.y_end - SLIDE_SIZE.y_start - 2) * factor:
            return False
        return True

    def check_img_border(top_y):
        for x in range(SLIDE_SIZE.x_start, imgsrc.width - SLIDE_SIZE.x_end):
            if check_column_white_scale(x):
                if x + SLIDE_SIZE.width - SLIDE_SIZE.x_start < imgsrc.width:
                    if check_column_white_scale(x + SLIDE_SIZE.x_end - SLIDE_SIZE.x_start - 1):
                        if check_inner_black_scale(x):
                            if check_row_white_scale(x, top_y + SLIDE_SIZE.y_end - SLIDE_SIZE.y_start - 1):
                                if check_row_white_scale(x, top_y):
                                    return x

                else:
                    break
        return None

    retval = check_img_border(top)
    if not retval:
        retval = check_img_border(top + 1)
        if not retval:
            retval = check_img_border(top - 1)
    if retval is not None:
        return retval
    raise RuntimeError('cannot find a matching block.')


from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from urllib.parse import urlparse, urljoin
from math import ceil, pow, sqrt
import threading

url_page_format = 'http://glidedsky.com/level/web/crawler-captcha-1?page=%d'


def get_data_from_url(url, max_retries=10):
    headers = simple_spider.HEADERS.copy()
    del headers['Cookie']
    while True:
        try:
            req = requests.get(url, timeout=10)
            return req.content
        except requests.exceptions.RequestException:
            max_retries -= 1
            if max_retries < 0:
                raise TimeoutError()
            time.sleep(0.5)
            continue


def generate_slide_locus(distance, accelerate_scale, total_time=1, interval=15):
    locus_len = int(ceil(distance / interval))
    accelerate = int(locus_len * accelerate_scale)
    decelerate = locus_len - accelerate
    # locus_data = [0]
    acc_time = total_time * accelerate_scale      # assume
    # a = 2x / t^2
    a = 2*(distance * accelerate_scale) / pow(acc_time, 2)
    time_interval = acc_time / accelerate
    for i in range(accelerate):
        yield int(
            0.5 * a * pow((i+1) * time_interval, 2)
        )
    v = a * acc_time
    dec_time = total_time * (1-accelerate_scale)        # assume
    # a = 2x / t^2
    a = 2*(distance * (1-accelerate_scale)) / pow(dec_time, 2)
    time_interval = dec_time / decelerate
    dec_start = distance * accelerate_scale
    for i in range(decelerate):
        yield int(
            dec_start + v * (i+1) * time_interval - 0.5 * a * pow((i+1) * time_interval, 2)
        )


def pass_captcha(browser):
    # try:
    WebDriverWait(browser, 10).until(
        expected_conditions.presence_of_element_located((By.ID, "tcaptcha_iframe"))
    )
    browser.switch_to.frame('tcaptcha_iframe')
    WebDriverWait(browser, 10).until(
        expected_conditions.presence_of_element_located((By.ID, "slideBg"))
    )
    WebDriverWait(browser, 10).until(
        expected_conditions.presence_of_element_located((By.ID, "slideBlock"))
    )
    img_bg = browser.find_element_by_id('slideBg')
    img_slide = browser.find_element_by_id('slideBlock')
    try:
        bg_src = wait_attribute_get(img_bg, 'src')
        slide_position = wait_attribute_get(img_slide, 'style', contain='top')
    except TimeoutError:
        raise

    # load image background
    bg_urlparse = urlparse(bg_src)
    if not bg_urlparse.scheme:
        bg_src = urljoin('https://hy.captcha.qq.com', bg_urlparse.geturl())

    img_fp = BytesIO(get_data_from_url(bg_src))
    imgsrc, pixels = img_threshold(img_fp)
    # imgsrc, pixels = img_threshold(img_fp, 'hahahahaha.jpg')

    rex = re.compile('top:\s*(\d+)px')
    slide_top = int(rex.search(slide_position).group(1)) * 2
    rex = re.compile('left:\s*(\d+)px')
    slide_left = int(rex.search(slide_position).group(1)) * 2
    block_border = scan_gap_position(imgsrc, pixels, slide_top + SLIDE_SIZE.y_start)

    drag_thumb = browser.find_element_by_id('tcaptcha_drag_thumb')
    action_chains = ActionChains(browser)
    action_chains.click_and_hold(drag_thumb)
    distance = (block_border - SLIDE_SIZE.x_start - slide_left) / 2

    last_offset = 0
    for i in generate_slide_locus(distance, 0.8, interval=15):
        action_chains.move_by_offset(int(i - last_offset), 0)

        last_offset = i
        # time.sleep(0.5)
    action_chains.release()
    action_chains.perform()

    # except:
    #     # print_exc()
    #     raise


def wait_attribute_get(ele, attr_name, contain=None, interval_time=0.3, max_retries=20):
    retry_cnt = 0
    while True:
        if retry_cnt >= max_retries:
            raise TimeoutError()
        time.sleep(interval_time)
        attr_val = ele.get_attribute(attr_name)
        if attr_val:
            if contain is not None:
                if contain not in attr_val:
                    continue
            return attr_val
        retry_cnt += 1


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('---headless')


class Spider(simple_spider.BasicSpider):
    def build_browser(self):
        while True:
            browser = webdriver.Chrome(
                executable_path="./drivers/chromedriver.exe",
                options=chrome_options
            )
            browser.set_page_load_timeout(20)
            browser.set_script_timeout(20)
            try:
                browser.get('http://glidedsky.com/login')
                cookie_list = [i.split('=') for i in simple_spider.HEADERS['Cookie'].split(';')]
                for k, v in cookie_list:
                    browser.add_cookie({'name': k.strip(), 'value': v.strip()})
            except WebDriverException:
                browser.quit()
            else:
                break

        return browser

    def _spider_handler(self, page, **kwargs):
        if not kwargs.get('browser', None):
            browser = self.build_browser()
            kwargs['browser'] = browser
        while not self._addup_wrapper(page, **kwargs):
            pass
        self._queue.put_nowait((page, kwargs))

    def get_page_addup(self, page, **kwargs):
        browser = kwargs.get('browser', None)
        browser.get(url_page_format % page)

        try:
            pass_captcha(browser)
        except:
            raise
        else:
            WebDriverWait(browser, 20).until(
                expected_conditions.presence_of_element_located((By.CLASS_NAME, "col-md-1"))
            )
            bs4 = simple_spider.BeautifulSoup(browser.page_source, 'lxml')
            if int(bs4.find('li', attrs={'class': 'page-item active'}).string) != page:
                raise KeyError('unmatched page number.')
            counter = 0
            for i in bs4.find_all('div', attrs={'class': 'col-md-1'}):
                counter += int(i.string.strip())

            print(counter)
            self.page_number_data[page - 1] = counter

    def _task_controller(self):
        task_done_counter = 0
        while True:
            page, extra_kw = self._queue.get()
            browser = extra_kw.get('browser', None)
            self._queue.task_done()
            task_done_counter += 1

            print(page, task_done_counter)
            if not self.next_page % 10:
                self.save_addup_data("./data/%s.txt" % time.perf_counter())
            if task_done_counter + self.start_page - 1 >= self.max_page:
                self.save_addup_data('data%d.txt' % time.time())
                print(self.get_total())
                break
            else:
                if self.next_page <= self.max_page:
                    print('NEXT_PAGE: %d' % self.next_page)
                    if browser:
                        browser.execute_script('window.stop ? window.stop() : document.execCommand("Stop");')
                    self._run_next_page({'browser': browser})
                else:
                    browser.quit()

    def run(self):

        for i in range(self.max_task):
            self._run_next_page()
            time.sleep(5)

        ctrl = threading.Thread(target=self._task_controller, name='task_controller')
        ctrl.start()

        # for inspection
        while True:
            time.sleep(1)


if __name__ == '__main__':
    spider = Spider(2, url_page_format)
    spider.run()
    while True:
        time.sleep(1)
