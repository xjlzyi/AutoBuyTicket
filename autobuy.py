# -*- coding: utf-8 -*-

import re
import urllib2
import sys
from PIL import Image
import ssl

#关闭证书验证
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

class WebHelper:
    def __init__(self):
        self.username = ''
        self.password = ''
        self.loginurl = 'https://kyfw.12306.cn/otn/login/init'
        self.pic_url = 'https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=login&rand=sjrand&0.21191171556711197'
        self.user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        self.parse_img_url = 'http://stu.baidu.com/n/image?fr=html5&needRawImageUrl=true&id=WU_FILE_0&name=233.png&type=image%2Fpng&lastModifiedDate=Mon+Mar+16+2015+20%3A49%3A11+GMT%2B0800+(CST)&size='

    def loginWeb(self, url):
        pass

    def get_img(self):
        response = urllib2.urlopen(self.pic_url)
        raw = response.read()
        with open('./temp.jpg', 'wb') as fp:
            fp.write(raw)
        return Image.open('./temp.jpg')

    def get_sub_img(self, im, x, y):
        assert 0 <= x <= 3
        assert 0 <= y <= 2
        width = height = 68
        left = 5 + (67 + 5) * x
        top = 41 + (67 + 5) * y
        right = left + 67
        bottom = top + 67
        return im.crop((left, top, right, bottom))

    def baidu_image_upload(self, im):
        url = "http://image.baidu.com/pictureup/uploadshitu?fr=flash&fm=index&pos=upload"

        im.save("./query_temp_img.png")
        raw = open("./query_temp_img.png", 'rb').read()

        files = {
            'fileheight'   : "0",
            'newfilesize'  : str(len(raw)),
            'compresstime' : "0",
            'Filename'     : "image.png",
            'filewidth'    : "0",
            'filesize'     : str(len(raw)),
            'filetype'     : 'image/png',
            'Upload'       : "Submit Query",
            'filedata'     : ("image.png", raw)
        }

        resp = requests.post(url, files=files, headers={'User-Agent':self.user_agent})

        #  resp.url
        redirect_url = "http://image.baidu.com" + resp.text
        return redirect_url

    def parse_img(self, im):       
        im.save('./temp_img.png')
        raw = open('./temp_img.png', 'rb').read()
        url = self.parse_img_url + str(len(raw))
        request = urllib2.Request(url, raw, {'Content-Type': 'image/png', 'User-Agent': self.user_agent})
        response_url = urllib2.urlopen(request).read()

        url = "http://image.baidu.com/n/pc_search?queryImageUrl=" + urllib2.quote(response_url)
        request = urllib2.Request(url, headers={'User-Agent': self.user_agent})
        response = urllib2.urlopen(request)
        html = response.read()
        return self.baidu_stu_html_extract(html) 

    def baidu_stu_html_extract(self, html):  
        pattern = re.compile(r"'multitags':\s*'(.*?)'")  
        matches = pattern.findall(html)  
        if not matches:  
            return '[UNKOWN]'  
        tags_str = matches[0]
        result =  list(filter(None, tags_str.replace('\t', ' ').split()))
        return '|'.join(result) if result else '[UNKOWN]'


if __name__ == '__main__':
    helper = WebHelper()
    im = helper.get_img()
    for i in range(2):
        for y in range(4):
            im2 = helper.get_sub_img(im, y, i)
            result = helper.parse_img(im2)
            print((y, i), result)