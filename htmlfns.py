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
    html=getraw('www.google.com')
    scraper=ImageScraper()
    # html='<html><t>erg</t></html>' #<!doctype html>
    # log.info(html.data)
    # log.info(html.data.decode())
    scraper.feed(html)
    log.info("Found {} images: {}".format(len(scraper.images),scraper.images))
    dir='images/openclipart.com/'+'_'.join(glosses)
    file.makedir(dir)
    for i in [i for i in scraper.images
                        if 'openclipart-logo-2019.svg' not in i]:#[1:5]:
        url=imgurl(i['src'])
        num=i['src'].split('/')[-1]
        filename='_'.join([num,i['alt']])
        log.info("{} ({})".format(url,filename))
        response=getbinary(url)
        log.info("response data type: {}".format(type(response)))
        fqdn=file.getdiredurl(dir,filename)
        with open(fqdn,'wb') as d:
            d.write(response)

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
