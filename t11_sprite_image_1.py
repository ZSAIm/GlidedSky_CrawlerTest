
import simple_spider
import re
from io import BytesIO
import base64
from PIL import Image

THRESHOLD = 250


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


def split_img_number(pixels, width, height):
    def find_next_white_column(start_x):
        for x in range(start_x, width):
            for y in range(height):
                if pixels[x, y] < 200:
                    break
            else:
                return x
        raise ValueError('split_img_number')

    def find_next_black_column(start_x):
        for x in range(start_x, width):
            for y in range(height):
                if pixels[x, y] < 200:
                    return x

    right_border_list = [0]

    black_start_x = find_next_black_column(0)
    # 0 right border
    white_start_x = find_next_white_column(black_start_x)
    right_border_list.append(white_start_x)
    for i in range(9):
        black_start_x = find_next_black_column(white_start_x)
        white_start_x = find_next_white_column(black_start_x)
        right_border_list.append(white_start_x)

    return right_border_list


def collect_css(bs4, spcific_style_name=None):
    css_collect = {}
    css_res = None
    rex_css = re.compile('\.(.*?)\s*{\s*(.*?):(.*?)\s*}')
    for i in bs4.find_all('style'):
        res = rex_css.findall(i.text)
        if res:
            css_res = res

    if not css_res:
        raise ValueError('cannot find target css.')

    # collect css attr
    for i in css_res:
        class_name = i[0]
        if ':' in class_name:
            class_name = class_name[:class_name.index(':')]
        if spcific_style_name is None:
            if class_name in css_collect:
                css_collect[class_name].append(tuple(i[1:]))
            else:
                css_collect[class_name] = []
                css_collect[class_name].append(tuple(i[1:]))
        else:
            if i[1] == spcific_style_name:
                css_collect[class_name] = i[2]

    return css_collect


def find_all_used_css(bs4):
    used_css = []
    for i in bs4.find_all('div', attrs={'class': 'col-md-1'}):
        for num_tag in i.find_all('div'):
            name = num_tag.get('class')[0]
            if name not in used_css:
                used_css.append(name)
    return used_css


# def sort_sprite_css_name(css_name_position_x):


class Spider(simple_spider.BasicSpider):
    def get_page_addup(self, page, **kwargs):
        def parse_sprite_number(div_tags):
            num_str_list = []
            for i in div_tags:
                for index, border_x in enumerate(right_border_x_list):
                    cur_pos_x = abs(int(css_collect[i.get('class')[0]][:-2]))
                    if index + 1 >= len(right_border_x_list):
                        raise RuntimeError('unknown error')
                    if border_x <= cur_pos_x < right_border_x_list[index + 1]:
                        num_str_list.append(str(index))
                        break

            return int(''.join(num_str_list))

        bs4 = self.get_bs4(page)
        if int(bs4.find('li', attrs={'class': 'page-item active'}).string) != page:
            raise KeyError('unmatched page number.')

        css_collect = collect_css(bs4)
        base64_img_str = css_collect['sprite'][0][1].split('"')[1]
        img_fp = BytesIO(base64.b64decode(base64_img_str[base64_img_str.index(',')+1:].encode('utf-8')))
        imgsrc, pixels = img_threshold(img_fp)
        right_border_x_list = split_img_number(pixels, imgsrc.width, imgsrc.height)
        css_collect = collect_css(bs4, 'background-position-x')

        counter = 0
        for i in bs4.find_all('div', attrs={'class': 'col-md-1'}):
            add = parse_sprite_number(i.find_all('div'))
            # print(add)
            counter += add

        self.page_number_data[page-1] = counter
        print(counter)


if __name__ == '__main__':
    url_page_format = 'http://glidedsky.com/level/web/crawler-sprite-image-1?page=%d'

    spider = Spider(10, url_page_format)

    spider.run()

