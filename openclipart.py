#!/usr/bin/env python3
# coding=UTF-8
import urllib.request
import urllib.parse
import secrets

class Client(object):
    def download(self,kw):
        with urllib.request.urlopen('http://python.org/') as response:
           html = response.read()
        return filenames
    def login(self):
        # curl -X POST https://openclipart.org/api/v2@beta/auth/login -d "username=kentlingdrc&password=<REDACTED>"
        data=self.builddata(username=secrets.username, password=secrets.password)
        # print("URL:",url)
        print("DATA:",data)
        tokendata=self.getpost('login',data)
        if tokendata:
            self.usertoken=tokendata['data']['token']
            print(self.usertoken)
            print(self.usertoken['data']['token'])
    def search(self, kw):
        data=self.builddata(q=kw, per_page=10, offset=1)
        tokendata=self.getpost('search',data)
        print(tokendata)
    def createapp(self):
        self.builddata(name="App")
        response=self.getpost("App",data)
        if response:
            self.apptoken=response['data']['token']
            self.appid=response['data']['app']['appid']
            self.appsecret=response['data']['app']['secret']
    def getpost(self, urlfn, data=None):
        url=self.buildurl(urlfn)
        # print("URL:",url)
        if self.headers and data:
            req = urllib.request.Request(url, data, headers=self.headers)
        elif self.headers:
            req = urllib.request.Request(url, headers=self.headers)
        elif data:
            req = urllib.request.Request(url, data)
        else:
            req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            print(e.code)
            print(e.read())
    def buildurl(self,fn):
        return self.url+self.api+self.cmd[fn]
    def builddata(self,**kwargs):
        data = urllib.parse.urlencode(kwargs)
        return data.encode('ascii') # data should be bytes
    def buildheaders(self):
        self.login()
        self.headers={"Authorization": "Bearer {}".format(self.usertoken)}
        self.headers['x-openclipart-apikey']=self.apptoken
    def __init__(self):
        self.url='https://openclipart.org'
        self.api='/api/v2-beta'
        self.cmd={
                'login':'/auth/login',
                'createapp':'/apps/create',
                'gettoken':'/apps/getToken',
                'search':'/search',
                'cliparts':'/cliparts'
                }
        self.headers={}
        super(Client, self).__init__()

if __name__ == "__main__":
    c=Client()
    # filenames=c.download("dog")
    c.login()
    # c.search('dog')
    # c.url='rasnet.lan'
    # # print(filenames)
