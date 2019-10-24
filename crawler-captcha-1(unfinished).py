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


from collections import namedtuple

CaptchaRouteRes = namedtuple('_CaptchaRouteRes', 'res start_time sendparams full_url')


def get_rnd():
    # Math.floor(1e6 * Math.random())
    return int(1e6 * random.random())


def get_rand():
    # Math.floor(1e8 * Math.random())
    return int(1e8 * random.random())


ua = "TW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSF" \
     "RNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzc2LjAuMzgwOS4xMzIgU2FmYXJpLzUzNy4zNg=="


cap_union_basic_params = {
    'aid': '2005597573',
    'accver': '1',
    'showtype': 'popup',
    'ua': ua,
    'noheader': '1',
    'fb': '1',
    'grayscale': '1',
    'clientype': '2',
    'cap_cd': '',
    'uid': '',
    'wxLang': '',
    'subsid': None,
    'sess': '',
}


cap_union_prehandle_url = 'https://ssl.captcha.qq.com/cap_union_prehandle'
cap_union_new_show_url = 'https://ssl.captcha.qq.com/cap_union_new_show'
dfpReg_url = 'https://dj.captcha.qq.com/dfpReg'

cap_union_prehandle_params = cap_union_basic_params.copy()
cap_union_prehandle_params['subsid'] = SUBSID_PREHANDLE

cap_post_redirect_url = 'https://ssl.captcha.qq.com/cap_union_new_verify'


cap_union_frame_addparams = {
    'fwidth': '0',
    'sid': None,
    'forcestyle': 'undefined',
    'tcScale': '1',
    'rnd': None,
    'TCapIframeLoadTime': 'undefined',
    'prehandleLoadTime': None,
    'createIframeStart': None,
}

cap_img_addparams = {
    'rand': None,
    'websig': None,
    'vsig': None,
    'img_index': None,
}



def get_captcha_prehandle():
    start = int(1000 * time.time())

    params = cap_union_basic_params.copy()
    params['subsid'] = SUBSID_PREHANDLE

    req = requests.get(cap_union_prehandle_url, params=cap_union_prehandle_params, headers=simple_spider.HEADERS)
    text = req.text
    res_json = json.loads(text[text.index('(')+1: text.rindex(')')])

    return CaptchaRouteRes(res=res_json, start_time=start, sendparams={}, full_url=req.url)


def get_cap_union_new_show(prehandle_res):
    start = int(1000 * time.time())

    params = cap_union_basic_params.copy()
    params['subsid'] = SUBSID_FRAME

    add = cap_union_frame_addparams.copy()
    add['prehandleLoadTime'] = str(start - prehandle_res.start_time)
    add['createIframeStart'] = str(start)
    add['rnd'] = str(get_rnd())
    add['sid'] = prehandle_res.res['sid']
    add['sess'] = prehandle_res.res['sess']

    params.update(add)
    headers = simple_spider.HEADERS.copy()
    headers['Referer'] = prehandle_res.full_url
    req = requests.get(cap_union_new_show_url, params=params, headers=headers)
    text = req.text
    rex_captchaConfig = re.compile('window\.captchaConfig\s*=\s*({.*?});')
    res = rex_captchaConfig.search(text)
    res_json = simple_spider.json_loads_js(res.group(1))
    return CaptchaRouteRes(res=res_json, start_time=start, sendparams=params, full_url=req.url)


def get_captcha_img(frame_res, index):
    start = int(1000 * time.time())
    params = frame_res.sendparams.copy()
    if index == IMG_INDEX_BG:
        params['subsid'] = SUBSID_BG
        cap_img_url = frame_res.res['cdnPic1']
    else:
        params['subsid'] = SUBSID_SLIDE
        cap_img_url = frame_res.res['cdnPic2']

    params['prehandleLoadTime'] = str(start - frame_res.start_time)
    params['createIframeStart'] = str(start)
    params['rnd'] = str(get_rnd())

    add = cap_img_addparams.copy()
    add['rand'] = str(get_rand())
    add['websig'] = frame_res.res['websig']
    add['vsig'] = frame_res.res['vsig']
    add['img_index'] = index

    params.update(add)

    headers = simple_spider.HEADERS.copy()
    headers['Referer'] = frame_res.full_url

    req = requests.get(cap_img_url, params=params, headers=headers)

    return req.content


"Chromium PDF Plugin::Portable Document Format::application/x-google-chrome-pdf~pdf;Chromium PDF Viewer::::application/pdf~pdf;Native Client::::application/x-nacl~,application/x-pnacl~;Shockwave Flash::Shockwave Flash 32.0 r0::application/x-shockwave-flash~swf,application/futuresplash~spl"
"Chromium PDF Plugin::Portable Document Format::application/x-google-chrome-pdf~pdf;Chromium PDF Viewer::::application/pdf~pdf;Native Client::::application/x-nacl~,application/x-pnacl~;Shockwave Flash::Shockwave Flash 32.0 r0::application/x-shockwave-flash~swf,application/futuresplash~spl"


def get_dfpreg_cookie_fpsig(frame_res):
    params = {}
    params_list = [
        simple_spider.HEADERS['User-Agent'], 'en-US', 1.8, 1.8, 24, 8, -480, 1, 1, 1,
        'u', 'function', 'u', 'Win32', 0,
        "0605b74623dc075bd296676b1535b2b4",
        "6a6476965e1bf1d8031a3e0c72354a1b",
        'a1f937b6ee969f22e6122bdb5cb48bde', 0,
        "acaec0f6a6f5ef357897138167344763",
        "10801920241080192024",
        "1;", "1;1;1;1;1;1;1;0;1;object32UTF-8", 0, '0;0',
        "5a2daef1f23cd3a9f3fb2478d616a6d2",
        "44100_2_1_0_2_explicit_speakers",
        "ANGLE(Intel(R)HDGraphics4600Direct3D11vs_5_0ps_5_0)",
        "8a64a458fda03999d2172363c7fe36da",
        "cee2ad1773391cdf6e49e9964bc7303c",
    ]
    params_list.extend(list(['0' for _ in range(20)]))
    for i, v in enumerate(params_list):
        params[str(i)] = v

    addparams = {
        'fesig': "10508305152603354224",
        'ut': random.randint(500, 3000),
        'appid': 0,
        'refer': 'https://ssl.captcha.qq.com/cap_union_new_show',
        'domain': 'ssl.captcha.qq.com',
        'fph': '',
        'fpv': '0.0.15',
        'ptcz': '',
    }

    params.update(addparams)

    headers = simple_spider.HEADERS.copy()
    del headers['Cookie']
    headers['Referer'] = frame_res.full_url
    req = requests.get(dfpReg_url, params=params, headers=headers)
    text = req.text
    return text[text.index('{'): text.rindex('}') + 1]






def send_captcha_log(mov_list):
    pass

# =====================================================
#                width * height     offset_x   offset_y
# slide size =     136 * 136            23         23
# bg    size =     680 * 390             0          0
# =====================================================


ImageInfo = namedtuple('ImageInfo', 'width height x_start x_end y_start y_end')

SLIDE_SIZE = ImageInfo(136, 136, 23, 136 - 24, 23, 136 - 24)
BG_SIZE = ImageInfo(680, 390, 0, 0, 0, 0)


def img_threshold(fp, name, threshold=200):

    img = Image.open(fp)
    limg = img.convert('L')
    pixels = limg.load()

    for y in range(limg.height):
        for x in range(limg.width):
            pixels[x, y] = 0 if pixels[x, y] < threshold else 255

    limg.save(name)
    return limg, pixels


def scan_column_white_number(pixels, x, y_start, y_end):
    white_counter = 0
    for y in range(y_start, y_end):
        if pixels[x, y] == 255:
            white_counter += 1
    return white_counter


def scan_inner_black_number(pixels, x_start, x_end, y_start, y_end):
    black_counter = 0
    for y in range(y_start, y_end+1):
        for x in range(x_start, x_end+1):
            if pixels[x, y] == 0:
                black_counter += 1

    return black_counter


def scan_gap_position(imgsrc, pixels, top):
    def check_white_scale(x, factor=0.50):
        """ Return True if half of pixels on the column are white. """
        # for x in range(imgsrc.width - SLIDE_SIZE.offset_x):
        white_cnt = scan_column_white_number(
            pixels, x,
            top,
            top + SLIDE_SIZE.y_end - SLIDE_SIZE.y_start
        )
        # print(x, white_cnt, (SLIDE_SIZE.y_end - SLIDE_SIZE.y_start) * factor)
        if white_cnt < (SLIDE_SIZE.y_end - SLIDE_SIZE.y_start) * factor:
            return False
        return True

    def check_inner_black_scale(x, factor=0.85):
        black_cnt = scan_inner_black_number(
            pixels, x + 1, x + SLIDE_SIZE.x_end - SLIDE_SIZE.x_start - 1,
                    top + 1,
                    top + SLIDE_SIZE.y_end - SLIDE_SIZE.y_start - 1
        )

        if black_cnt < (SLIDE_SIZE.x_end - SLIDE_SIZE.x_start - 2) * \
                (SLIDE_SIZE.y_end - SLIDE_SIZE.y_start - 2) * factor:
            return False
        return True

    for x in range(SLIDE_SIZE.x_start, imgsrc.width - SLIDE_SIZE.x_end):
        if check_white_scale(x):
            if x + SLIDE_SIZE.width - SLIDE_SIZE.x_start < imgsrc.width:
                # print('1 ->', x)
                if check_white_scale(x + SLIDE_SIZE.x_end - SLIDE_SIZE.x_start - 1):
                    # print('2 ->', x)
                    if check_inner_black_scale(x):
                        # print(x)
                        return x
                        # break

    raise RuntimeError('cannot find a matching block.')


cap_union_new_verify_script_prefix = """
const jsdom = require('jsdom');
const { JSDOM } = jsdom;
const resourceLoader = new jsdom.ResourceLoader({
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
});

build_tdc = function (e, t, n) {
    "use strict";
    var r = window.TDC;
    function o(e) {
        r.setData && r.setData(e)
    }
    function a() {
        return "function" == typeof r.getInfo && r.getInfo() || {}
    }
    e.exports = {
        link: function() {
            r = window.TDC || {}
        },
        setData: o,
        getData: function() {
            return o({
                ft: "qX_7P7n_H"
            }),
                "function" == typeof r.getData ? r.getData(!0) : "---"
        },
        clearData: function() {
            r.clearTc && r.clearTc()
        },
        getInfo: a,
        getToken: function() {
            return (a() || {}).tokenid || ""
        },
        getEks: function() {
            return (a() || {}).info || ""
        },
        getTlg: function() {
            return "undefined" == typeof window.TDC ? 0 : 1
        }
    }
}

function script_prepare(url, referrer){
    global.jsdom_instance = new JSDOM(``, {
        //url: "https://ssl.captcha.qq.com/cap_union_new_show?aid=2005597573&accver=1&showtype=popup&ua=TW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzc0LjAuMzcyOS4xNjkgU2FmYXJpLzUzNy4zNg%3D%3D&noheader=1&fb=1&grayscale=1&clientype=2&subsid=2&sess=J72FmwJIOUQ-z7yQH0WpD3pKoi_RFR7fhbFLxenT5PwEwtvf-KBLyCZmTRcc1ZiJ-0wovuRLDnLbXtO8HwESHCIyqIuHQ8REq533U9oEe7CmTAR0BL_BLWGguGjSAe229NbWrJWDyQDHo_xBQkWdgAIn99sh9IT4D9EMAdmnEzuBCZRO1SNLvSag7nt8SQUdbCG1gIO6iFzZ5IXbvMue7g**&fwidth=0&sid=6736072634424323050&forcestyle=undefined&wxLang=&tcScale=1&uid=&cap_cd=&rnd=126204&TCapIframeLoadTime=undefined&prehandleLoadTime=573&createIframeStart=1568364127477",
        url: url,
        //referrer: "http://glidedsky.com/level/web/crawler-captcha-1",
        referrer: referrer,
    
        contentType: "text/html",
        includeNodeLocations: true,
        storageQuota: 10000000,
        resources: resourceLoader
    });
    global.window = dom.window;
    global.document = window.document;
    global.navigator = window.navigator;
    global.screen = window.screen;
    window.Array = Array;
    
    global.tdc = {exports: {}};
    build_tdc(tdc, tdc.exports, null);
}
function tdc_set_data(data){
    tdc.exports.setData(data);
}
function set_slide_value(slide_value){
    tdc.exports.setData({
        trycnt: 0,
        refreshcnt: 0,
        slideValue: slide_value,
        dragobj: 0
    });
}

"""

cap_union_new_verify_script_postfix = """

tdc.exports.setData({clientType: "2"});

winevent_mouseup({x: 131, y: 288});
# need a time delay
winevent_touchend({x: 131, y: 288});

tdc.exports.setData([10, 62, 0.5]);
tdc.exports.setData([9.15, 61.40625, 0.5]);

slideval = [[83,286,12],[1,0,1],[1,0,3],[1,0,2],[1,0,2],[2,0,4],[2,0,4],[5,0,10],[2,0,1],[2,0,4],[3,0,3],[3,0,3],[2,0,5],[5,0,4],[4,0,4],[4,0,3],[3,0,6],[0,0,77]];

sec = {
    trycnt: 2,
    refreshcnt: 0,
    slideValue: slideval,
    dragobj: 1
};
tdc.exports.setData(sec);

"""

canvas_base64 =  "data:image/png;base64,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";


def verify_script_wrapper(script_text):
    def wrapper(pattern, group_index_list, replace_text_list):
        rex = re.compile(pattern, re.S)
        res = rex.search(wrapped_core)
        new_txt = wrapped_core
        for i, v in enumerate(group_index_list):
            new_txt = new_txt.replace(res.group(group_index_list[i]), replace_text_list[i])

        return new_txt



    wrapped_core = script_text[1:-3]
    # canvas true
    # rex_canvas_true = re.compile('return(\s*!\(!\w+\.getContext.*?)}', re.S)
    # res = rex_canvas_true.search(wrapped_core)
    # wrapped_core = wrapped_core.replace(res.group(1), 'true;')
    wrapped_core = wrapper('return(\s*!\(!\w+\.getContext.*?)}', [1], [' true;'])
    wrapped_core = wrapper('(var\s*\w+\s*=\s*\w+\.getContext\(\w+.*?\);)',
                           [1], ['return "%s";' % canvas_base64])
    wrapped_core = wrapper('(try\s*{\s*if\s*\(\w+\.getContext.*?catch\s*\(\w+\)\s*{\s*})',
                           [1], [' return !0;'])
    wrapped_core = wrapper('(var\s*\w+=\w+\.getExtension\(.*?\);)',
                           [1], [' return "ANGLE (Intel(R) HD Graphics 4600 Direct3D11 vs_5_0 ps_5_0)";'])
    wrapped_core = wrapper('exports\s*=\s*{\s*on\s*:\s*function\s*\(.*?\)\s*{(.*?)},',
                           [1], [' return "ANGLE (Intel(R) HD Graphics 4600 Direct3D11 vs_5_0 ps_5_0)";'])

    rex = re.compile('exports\s*=\s*{\s*on:\s*function\(.*?\)\s*{(.*?)},\s*get', re.S)
    for i in rex.findall(wrapped_core):
        print(i)

    # canvas base64 image
    rex_canvas_true = re.compile('return(\s*!\(!\w+\.getContext.*?)}', re.S)
    res = rex_canvas_true.search(wrapped_core)
    wrapped_core = wrapped_core.replace(res.group(1), 'true;')
    new_script = '{prefix};init_TDC={core}'.format(
        prefix=cap_union_new_verify_script_prefix,
        core=wrapped_core,
        # postfix=cap_union_new_verify_script_postfix
    )

    return new_script


def pass_captcha():
    pass













class Spider(simple_spider.BasicSpider):
    def get_page_addup(self, page):
        bs4 = self.get_bs4(page)

        css_action_set = build_css_action(bs4)

        counter = 0
        for i in bs4.find_all('div', attrs={'class': 'col-md-1'}):
            counter += parse_num_tag(css_action_set, i.find_all('div'))

        self.page_number_data[page-1] = counter


if __name__ == '__main__':
    with open('test_tdc.js', 'r') as f:
        script_text = f.read()
    verify_script_wrapper(script_text)

    exit()
    for i in range(10):
        prehandle_res = get_captcha_prehandle()
        time.sleep(0.1)
        frame_res = get_cap_union_new_show(prehandle_res)

        rate = 1
        slide_top = int(int(frame_res.res['spt']) * rate)
        time.sleep(0.1)
        img_src = get_captcha_img(frame_res, IMG_INDEX_BG)

        img_fp = BytesIO(img_src)
        imgsrc, pixels = img_threshold(img_fp, 'captcha/%03d-1.jpg' % i)
        print('%03d-1.jpg' % i)
        print(scan_gap_position(imgsrc, pixels, slide_top + SLIDE_SIZE.y_start))

        fp3_id1 = get_dfpreg_cookie_fpsig(frame_res)
        time.sleep(0.1)
        # with open('captcha/%03d-1.jpg' % i, 'wb') as f:
        #     f.write(img_src)
        # img_src = get_captcha_img(frame_res, IMG_INDEX_BLOCK)
        #
        # img_fp = BytesIO(img_src)
        # img_threshold(img_fp, 'captcha1/%03d-2.jpg' % i)

        # with open('captcha/%03d-2.jpg' % i, 'wb') as f:
        #     f.write(img)
        # time.sleep(1)
    # get_captcha_prehandle()
    exit()
    url_page_format = 'http://glidedsky.com/level/web/crawler-captcha-1?page=%d'

    spider = Spider(1, url_page_format)
    spider.run()
