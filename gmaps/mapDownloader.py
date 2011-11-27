#!/usr/bin/env python
#-*- coding:utf-8 -*-
'''
Created on 2011-11-12

@author: "Yang Junyong <yanunon@gmail.com>"
'''

import random
import re
import os
import time
from threading import Thread, Lock

import mapTool
import urlFetcher
import mapFile


class DownloadMap(object):
    '''
    classdocs
    '''

    layer_url = {}

    def __init__(self, http_proxy=None):
        '''
        Constructor
        '''
        self.fetcher = urlFetcher.UrlFetcher(http_proxy=http_proxy)
        
    #http://mt%d.google.com/vt/lyrs=m@163000000&hl=zh-CN&x=%d&y=%d&z=%i
    def __parse_google_maps__(self, layer):
        map_server_query = {"gmap":"m", "ghyb":"h", "gsat":"k", "gter":"p"}
        basic_url = 'http://maps.google.com/maps?t=%s&hl=%s' % (map_server_query[layer], 'zh-CN')
        
        html = self.fetcher.do_fetch(basic_url)
        
        if not html:
            return None
        
        hybrid = ''
        if layer == 'ghyb':
            hybrid = 'Hybrid'
            
        pattern = '<div id=inlineTiles'+ hybrid +' dir=ltr><img src="http://([a-z]{2,3})[0-9].google.com/(.+?)&'
        match = re.search(pattern, html)
        if match is not None:
            #print tuple(match.groups())
            return_url = 'http://%s%%d.google.com/%s' % tuple(match.groups())
            return_url +='&hl=zh-CN&x=%d&y=%d&z=%i'
            return return_url
        else:
            return None
    
    def download(self, layer, x, y, z):
        if layer not in self.layer_url.keys():
            self.layer_url[layer] = self.__parse_google_maps__(layer)
        fetch_url = self.layer_url[layer] % (random.randrange(4), x, y, z)
        #print fetch_url
        return self.fetcher.do_fetch(fetch_url)

class DownloadTask:
    
    def __init__(self, layer, x, y, z, overwrite=False):
        self.layer = layer
        self.x = x
        self.y = y
        self.z = z
        self.overwrite = overwrite

class TaskQueue:
    
    def __init__(self):
        self.stack = []
        self.lock = Lock()
        self.join_lock = Lock()
        self.length = 0
        self.stop_all = False
        self.unfinished = 0
        
    def get(self):
        task = -1
        self.lock.acquire()
        try:
            if self.length > 0:
                task = self.stack.pop()
                self.length -= 1
            elif self.stop_all:
                task = None
        finally:
            self.lock.release()
        
#        self.join_lock.acquire()
#        try:
#            if self.stop_all:
#                task = None
#        finally:
#            self.join_lock.release()
            
        return task
    
    def put(self, task):
        self.lock.acquire()
        try:
            self.stack.append(task)
            self.length += 1
            self.unfinished += 1
        finally:
            self.lock.release()
    
    def getSize(self):
        length = -1
        self.lock.acquire()
        try:
            length = self.length
        finally:
            self.lock.release()
        return length
    
    def finish_one(self):
        self.lock.acquire()
        try:
            self.unfinished -= 1
        finally:
            self.lock.release()
    
    def join(self):
        self.lock.acquire()
        try:
            while self.unfinished > 0:
                self.lock.release()
                time.sleep(0.1)
                self.lock.acquire()
        finally:
            self.lock.release()
    
    def stop(self):
        self.join()
        self.lock.acquire()
        try:
            self.stop_all = True
            self.length = 0
        finally:
            self.lock.release()
        
    
class DownloadThread(Thread):
    
    def __init__(self, file_lock, task_queue, name=None):
        Thread.__init__(self, name=name)
        self.downloadMap = DownloadMap()
        self.lock = file_lock
        self.task_queue = task_queue
        
    def run(self):
        while True:
            task = self.task_queue.get()
            if task is None:
                return
            elif task == -1:
                time.sleep(0.1)
                continue
            
            file_data = self.downloadMap.download(task.layer, task.x, task.y, task.z)
            print 'Thread:%s download map layer %s x:%d y:%d z:%d' % (self.name, task.layer, task.x, task.y, task.z)
            if file_data:
                self.lock.acquire()
                try:
                    mapFile.save_map_file(file_data, task.x, task.y, task.z, task.layer, task.overwrite)
                finally:
                    self.lock.release()
                self.task_queue.finish_one()

class MapDownloader:
    
    def __init__(self, thread_num=5):
        self.file_lock = Lock()
        self.task_queue = TaskQueue()
        self.threads = []
        self.thread_num = thread_num
        for i in range(self.thread_num):
            thread = DownloadThread(self.file_lock, self.task_queue, '[%d]' % i)
            self.threads.append(thread)
            thread.start()
            
    def dl_region(self, xmin, xmax, ymin, ymax, zoom, layer):
        world_tiles = 1 << zoom
        if xmax - xmin >= world_tiles:
            xmin, xmax = 0, world_tiles-1
        if ymax - ymin >= world_tiles:
            ymin, ymax = 0, world_tiles-1
        
        for i in xrange((xmax - xmin+world_tiles)%world_tiles + 1):
            x = (xmin + i)%world_tiles
            for j in xrange((ymax - ymin+world_tiles)%world_tiles + 1):
                y = (ymin + j)%world_tiles
                if not os.path.exists(mapFile.get_tile_path(layer, x, y, zoom)[1]):
                    task = DownloadTask(layer, x, y, zoom)
                    self.task_queue.put(task)
        #for thread in self.threads:
        #    thread.start()
                    
    def dl_location(self, top_left, bottom_right, zoom, layer):
        top_left_tile = mapTool.coord_to_tile((top_left[0], top_left[1], zoom))
        bottom_right_tile = mapTool.coord_to_tile((bottom_right[0], bottom_right[1], zoom))
        
        xmin = top_left_tile[0][0]
        ymin = top_left_tile[0][1]
        
        xmax = bottom_right_tile[0][0]
        ymax = bottom_right_tile[0][1]
        self.dl_region(xmin, xmax, ymin, ymax, zoom, layer)
    
    def wait_thread_done(self):
        self.task_queue.join()
    
    def stop_all(self):
        self.task_queue.stop()
        for thread in self.threads:
            thread.join()
            
if __name__ == '__main__':
    #d = downloadMap('gmap')
    d = MapDownloader(10)
    top_left = (45, 80)
    bottom_right = (30, 135)
    layer = 'gmap'
    zoom = 8
    #time.sleep(10)
    d.dl_location(top_left, bottom_right, zoom, layer)
    for thread in d.threads:
        thread.join()
    map = mapFile.merge_location_image(top_left, bottom_right, zoom, layer)
    map.show()
    map.save('test.png')
    