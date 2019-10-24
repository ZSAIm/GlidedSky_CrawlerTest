
import simple_spider
import re


def build_css_action(bs4):
    css_action_set = {}
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
        if class_name in css_action_set:
            css_action_set[class_name].append(tuple(i[1:]))
        else:
            css_action_set[class_name] = []
            css_action_set[class_name].append(tuple(i[1:]))

    # analyze css action
    # ========attr========
    # 1. opacity
    # 2. ::before
    # 3. float:left
    # 4. left: 1em or 2em
    # ===================

    for k, v in css_action_set.items():
        repval = None
        for attr in v:
            if attr[0] == 'content':
                repval = Action(id=ID_FULL_CONTENT, content=int(attr[1].strip('"').strip("'")), relative=False)
            elif attr[0] == 'opacity':
                repval = Action(id=ID_DISAPPEAR, content=None, relative=True)
            elif attr[0] == 'left':
                repval = Action(id=ID_LEFT_SHIFT, content=int(attr[1][:-2]), relative=True)
            elif attr[0] == 'float':
                if attr[1] != 'left':
                    raise ValueError('unknown type of float. (%s)' % attr[1])

        if not repval:
            repval = Action(id=ID_STILL, content=None, relative=False)

        css_action_set[k] = repval

    return css_action_set



def parse_num_tag(css_action_set, num_div_tag):

    # first glance
    num_list = []
    for i, tag in enumerate(num_div_tag):
        class_name = tag.get('class')[0]
        if class_name not in css_action_set:
            raise ValueError('cannot find class %s' % tag.get('class'))
        num_list.append(NumberIndex(index=i, content=tag.text, relative=False))
        action = css_action_set[class_name]
        numbi = num_list[i]
        num_list[i] = NumberIndex(index=numbi.index, content=numbi.content, relative=action.relative)

    for index, tag in enumerate(num_div_tag):
        class_name = tag.get('class')[0]
        if class_name not in css_action_set:
            raise ValueError('cannot find class %s' % tag.get('class'))
        action = css_action_set[class_name]
        numbi = num_list[index]
        num_list[index] = NumberIndex(index=numbi.index, content=numbi.content, relative=action.relative)

        if action.id == ID_DISAPPEAR:
            num_list[index] = NumberIndex(index=numbi.index, content=None, relative=True)
        elif action.id == ID_STILL:
            pass
        elif action.id == ID_LEFT_SHIFT:
            target_index = numbi.index + action.content
            for i, v in enumerate(num_list):
                if i != index:
                    if int(action.content) < 0:
                        if target_index <= v.index < index:
                            if num_list[i].relative and num_list[i].content is not None:
                                num_list[i] = NumberIndex(index=v.index + 1,
                                                          content=v.content, relative=v.relative)

                    else:
                        if target_index >= v.index > index:
                            if num_list[i].relative and num_list[i].content is not None:
                                num_list[i] = NumberIndex(index=v.index - 1,
                                                          content=v.content, relative=v.relative)

            num_list[index] = NumberIndex(index=target_index,
                                          content=numbi.content, relative=numbi.relative)

        elif action.id == ID_FULL_CONTENT:
            num_list[index] = NumberIndex(index=numbi.index,
                                          content=action.content, relative=numbi.relative)

    num_list = sorted(num_list, key=lambda x: x.index)
    for i, v in enumerate(num_list):
        if v.content is None:
            num_list[i] = None


    try:
        while True:
            num_list.remove(None)
    except ValueError:
        pass

    str_list = [str(i.content) for i in num_list]

    return int(''.join(str_list))


from collections import namedtuple

NumberIndex = namedtuple('NumberIndex', 'index content relative')

Action = namedtuple('_CssAction', 'id content relative')

ID_DISAPPEAR = -1
ID_STILL = 0
ID_LEFT_SHIFT = 1
ID_FULL_CONTENT = 2


class Spider(simple_spider.BasicSpider):
    def get_page_addup(self, page, **kwargs):
        bs4 = self.get_bs4(page)
        if int(bs4.find('li', attrs={'class': 'page-item active'}).string) != page:
            raise KeyError('unmatched page number.')

        css_action_set = build_css_action(bs4)
        counter = 0
        for i in bs4.find_all('div', attrs={'class': 'col-md-1'}):
            counter += parse_num_tag(css_action_set, i.find_all('div'))

        self.page_number_data[page-1] = counter


if __name__ == '__main__':
    url_page_format = 'http://glidedsky.com/level/web/crawler-css-puzzle-1?page=%d'

    spider = Spider(1, url_page_format)
    spider.run()

