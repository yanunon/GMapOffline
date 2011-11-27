#!/usr/bin/env python
#-*- coding:utf-8 -*-
'''
Created on 2011-11-13

@author: "Yang Junyong <yanunon@gmail.com>"
'''

import urllib2

class UrlFetcher(object):
    '''
    classdocs
    '''
    
    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.904.0 Safari/535.7'

    def __init__(self, http_proxy=None):
        '''
        Constructor
        '''
        self.http_proxy = http_proxy
        self.headers = {'User-Agent' : self.user_agent}
        
        if http_proxy:
            urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler(self.http_proxy)))
        
    def do_fetch(self, url):
        req = urllib2.Request(url=url, headers=self.headers)
        s = None
        try:
            rsp = urllib2.urlopen(req)
            s = rsp.read()
            rsp.close()
        except:
            s = None
        return s
        
        
        
