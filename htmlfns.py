#!/usr/bin/env python3
# coding=UTF-8
import logsetup
log=logsetup.getlog(__name__)
import html.parser
import file
import urls

"""general download functions"""
def getdecoded(url, **kwargs):
    r=urls.http.request("GET", url, **kwargs)
    if r.status == 200:
        return r.data.decode()
def getbinary(url, **kwargs):
    r=urls.http.request("GET", url, **kwargs)
    if r.status == 200:
        return r.data
def getraw(url):
    return urls.http.request("GET", url)

class TranslationScraper(html.parser.HTMLParser):
    """Pulling this: <span jsname="FteS1d" class="jzUr5c" lang="fr">texte</span>
    """
    def handle_data(self,data):
        if self.capture:
            self.text[self.capturelang].append(data)
        # t=self.get_starttag_text()
        # if 'texte' in data:
        #     log.info(data)
        # if 'lang=' in t:
        #     log.info("{}: {}".format(t,data))
        #     if 'lang="{}"'.format(self.lang) in t:

    def handle_starttag(self, tag, attrs):
        # if tag == 'html':
        #     log.info("starting html ({})".format(kwargs))
        if tag == 'span' and [t[1] for t in attrs if t[0] =='lang']:
            self.capture=True
            self.capturelang=[t[1] for t in attrs if t[0] =='lang'][0]
                # self.text[lang].append(self.get_starttag_text())
        # elif tag == 'span':
        #     print(attrs)
        # elif [t for t in attrs if t[0] =='lang' and t[1] == self.lang]:
        #     print(self.get_starttag_text())
        # lang in attrs and attrs['lang'] == self.lang:
    def handle_endtag(self,tag):
        self.capture=False
    def __init__(self,lang):
        log.info('scraping')
        self.lang=lang
        self.capture=False
        super().__init__()
        self.text={lang:[],
                    'en':[]
                    }
class ImageScraper(html.parser.HTMLParser):
    """Subclassing to do what I want"""
    """Pulling out this: <img src="/image/800px/301653" alt="Athlete's Foot">"""
    def handle_starttag(self, tag, attrs):
        # if tag == 'html':
        #     log.info("starting html ({})".format(kwargs))
        if tag == 'img':
            self.images.append({k:v for k,v in attrs})
    # def handle_data(self, data):
    #     if self.get_starttag_text() == '<t>':
    #         log.info("do this")
    def __init__(self):
        super().__init__()
        self.images=[]
def imgurl(x):
    if '800px' in x:
        x=x.replace('800px','400px')
    if "./Openclipart - Clipping Culture_files" in x:
        x=x.replace("./Openclipart - Clipping Culture_files",'/image/400px')
    site='https://openclipart.org'
    return site+x
if __name__ == '__main__':
    import htmlfns #not normally used here
    # html=getraw('www.google.com')
    text='translation terms that I want to use'
    kwargs={
            'sl':'en', #search language
            'tl':'fr',  #translate to language
            'text':text,
            'op':'translate', #operation?
            }
    terms=urls.urlencode(kwargs)
    url='https://translate.google.com/?'+terms
    log.info("Looking in {}".format(url))
    html=htmlfns.getdecoded(url)
    with open('googletrans.html','w') as f:
        f.write(html)
    # 'https://translate.google.com/?sl=en&tl=fr&text=translation&op=translate')
    scraper=TranslationScraper(lang='fr')
    # html='<html><t>erg</t></html>' #<!doctype html>
    # log.info(html.data)
    # log.info(html.data.decode())
    scraper.feed(html)
    log.info("Found {} text elements: {}".format(len(scraper.text),scraper.text))
    # log.info("Found {} images: {}".format(len(scraper.images),scraper.images))
    # dir='images/openclipart.com/'+'_'.join(glosses)
    # file.makedir(dir)
    # for i in [i for i in scraper.images
    #                     if 'openclipart-logo-2019.svg' not in i]:#[1:5]:
    #     url=imgurl(i['src'])
    #     num=i['src'].split('/')[-1]
    #     filename='_'.join([num,i['alt']])
    #     log.info("{} ({})".format(url,filename))
    #     response=getbinary(url)
    #     log.info("response data type: {}".format(type(response)))
    #     fqdn=file.getdiredurl(dir,filename)
    #     with open(fqdn,'wb') as d:
    #         d.write(response)

    """Maybe for later"""
        # try:
        #     from BeautifulSoup import BeautifulSoup
        # except ImportError:
        #     from bs4 import BeautifulSoup
        # # html = #the HTML code you've written above
        # parsed_html = BeautifulSoup(html)
        # # print(parsed_html.body.find('div', attrs={'class':'container'}).text)
        # # html=lift.readxmltext(html)
        # log.info("response prettyprinted:")
        # lift.prettyprint(parsed_html.body)
