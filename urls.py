#!/usr/bin/env python3
# coding=UTF-8
import urllib.request as request
import urllib.parse as parse
urlencode=parse.urlencode
urlopen=request.urlopen
import urllib3
http = urllib3.PoolManager()
# resp = http.request
# urllib.request.Request
