#!/usr/bin/env python
#-*- coding:utf-8 -*-
'''
Created on 2011-11-12

@author: "Yang Junyong <yanunon@gmail.com>"
'''

import random
import os
import Image
import Queue
import StringIO
from threading import Thread, Lock

import mapTool
import urlFetcher

MAP_LAYERS = {
          'map_cn': 'http://mt%d.google.cn/vt/lyrs=m@216173479&hl=zh-CN&gl=CN&src=app&x=%d&y=%d&z=%d&s=G',
          'sat_cn': 'http://mt%d.google.cn/vt/lyrs=s@129&hl=zh-CN&gl=CN&src=app&x=%d&s=&y=%d&z=%d&s=Galileo',
          'road_cn': 'http://mt%d.google.cn/vt/imgtp=png32&lyrs=h@216009069&hl=zh-CN&gl=CN&src=app&x=%d&s=&y=%d&z=%d&s=Galile',
          'mixed_cn': '',
          }

MAP_LAYER_IMG_TYPE = {
            'map_cn': 'png',
            'sat_cn': 'jpg',
            'road_cn': 'png',
            'mixed_cn': 'jpg',
                       }

MAP_DIR = 'maps'

class MapTile:
    
    def __init__(self, layer, x, y, z):
        self.layer = layer
        self.x = x
        self.y = y
        self.z = z
    
    def get_url(self):
        url = []
        if self.layer in MAP_LAYERS.keys():
            if self.layer == 'mixed_cn':
                url.append(MAP_LAYERS['sat_cn'] % (random.randrange(4), self.x, self.y, self.z))
                url.append(MAP_LAYERS['road_cn'] % (random.randrange(4), self.x, self.y, self.z))
            else:
                url.append(MAP_LAYERS[self.layer] % (random.randrange(4), self.x, self.y, self.z))
        return url
    
    def get_file_path(self):
        world_tile = 1 << self.z
        x = self.x % world_tile
        folder_list = [MAP_DIR, self.layer, str(self.z), str(x/1024), str(x%1024), str(self.y/1024)]
        file_name = "%d.%s" % (self.y%1024 , MAP_LAYER_IMG_TYPE[self.layer])
        file_path = ''
        for folder in folder_list:
            file_path = os.path.join(file_path, folder)
        file_path = os.path.join(file_path, file_name)
        return file_path
    
def get_location_tiles(top_left, bottom_right, zoom, layer):
    top_left_tile = mapTool.coord_to_tile((top_left[0], top_left[1], zoom))
    bottom_right_tile = mapTool.coord_to_tile((bottom_right[0], bottom_right[1], zoom))
    
    xmin = top_left_tile[0][0]
    ymin = top_left_tile[0][1]
    
    xmax = bottom_right_tile[0][0]
    ymax = bottom_right_tile[0][1]
    
    world_tiles = 1 << zoom
    if xmax - xmin >= world_tiles:
        xmin, xmax = 0, world_tiles-1
    if ymax - ymin >= world_tiles:
        ymin, ymax = 0, world_tiles-1

    tiles = []
    for i in xrange((xmax - xmin+world_tiles)%world_tiles + 1):
        x = (xmin + i)%world_tiles
        for j in xrange((ymax - ymin+world_tiles)%world_tiles + 1):
            y = (ymin + j)%world_tiles
            tile = MapTile(layer, x, y, zoom)
            tiles.append(tile)
    
    return tiles
    
def merge_location_image(top_left, bottom_right, zoom, layer):
    top_left_tile = mapTool.coord_to_tile((top_left[0], top_left[1], zoom))
    bottom_right_tile = mapTool.coord_to_tile((bottom_right[0], bottom_right[1], zoom))
    
    xmin = top_left_tile[0][0]
    ymin = top_left_tile[0][1]
    
    xmax = bottom_right_tile[0][0]
    ymax = bottom_right_tile[0][1]
    
    world_tiles = 1 << zoom
    if xmax - xmin >= world_tiles:
        xmin, xmax = 0, world_tiles-1
    if ymax - ymin >= world_tiles:
        ymin, ymax = 0, world_tiles-1
    
    width = (xmax - xmin+world_tiles)%world_tiles + 1
    height = (ymax - ymin+world_tiles)%world_tiles + 1
    map_image = Image.new("RGB", (width*256,height*256))
    for i in xrange(width):
        x = (xmin + i)%world_tiles
        for j in xrange(height):
            y = (ymin + j)%world_tiles
            tile = MapTile(layer, x, y, zoom)
            file_path = tile.get_file_path()
            if os.path.exists(file_path):
                paste_box = (i*256, j*256, (i+1)*256, (j+1)*256)
                paste_im = Image.open(file_path)
                map_image.paste(paste_im, paste_box)
            if layer == 'sat_cn':
                tile = MapTile('road_cn', x, y, zoom)
                file_path = tile.get_file_path()
                if os.path.exists(file_path):
                    #paste_box = (i*256, j*256, (i+1)*256, (j+1)*256)
                    paste_im = Image.open(file_path)
                    map_image.paste(paste_im, paste_box, paste_im)
    return map_image

class DownloadThread(Thread):
    
    def __init__(self, task_queue, lock, name=None, http_proxy=None):
        Thread.__init__(self, name=name)
        self.fetcher = urlFetcher.UrlFetcher(http_proxy=http_proxy)
        self.task_queue = task_queue
        self.folder_lock = lock
        self.running = True
        
    def run(self):
        while self.running:
            try:
                task = self.task_queue.get(True, 1)
                file_path = task.get_file_path()
                if not os.path.exists(file_path):
                    folder_path = os.path.dirname(file_path)
                    self.folder_lock.acquire()
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)
                    self.folder_lock.release()
                    
                    fetch_url = task.get_url()
                    file_data = self.fetcher.do_fetch(fetch_url[0])
                    if task.layer == 'mixed_cn':
                        file_data_2 = self.fetcher.do_fetch(fetch_url[1])
                        buf = StringIO.StringIO()
                        buf.write(file_data)
                        buf.seek(0)
                        img = Image.open(buf)
                        
                        buf2 = StringIO.StringIO()
                        buf2.write(file_data_2)
                        buf2.seek(0)
                        img2 = Image.open(buf2)
                        img.paste(img2, (0, 0, 256, 256), img2)
                        
                        buf.close()
                        buf2.close()
                        img.save(file_path)
                    else:
                        file = open(file_path, 'wb')
                        file.write(file_data)
                        file.close()
                self.task_queue.task_done()
            except Queue.Empty:
                pass
                
                
    def stop(self):
        self.running = False

class MapDownloader:
    
    def __init__(self, thread_num=5):
        self.task_queue = Queue.Queue()
        self.threads = []
        self.thread_num = thread_num
        self.lock = Lock()
        
        for i in range(self.thread_num):
            thread = DownloadThread(self.task_queue, self.lock, '[%d]' % i)
            self.threads.append(thread)
            thread.start()
                    
    def dl_location(self, top_left, bottom_right, zoom, layer):
        tiles = get_location_tiles(top_left, bottom_right, zoom, layer)
        for tile in tiles:
            self.task_queue.put(tile)
    
    def wait_thread_done(self):
        self.task_queue.join()
        for thread in self.threads:
            thread.stop()
            
if __name__ == '__main__':
    #d = downloadMap('gmap')
    d = MapDownloader(10)
    top_left = (39.922787,116.391925)
    bottom_right = (39.914016,116.401452)
    layer = 'mixed_cn'
    zoom = 18
    #time.sleep(10)
    d.dl_location(top_left, bottom_right, zoom, layer)
    d.wait_thread_done()
    
    #for thread in d.threads:
    #    thread.join()
    map = merge_location_image(top_left, bottom_right, zoom, layer)
    map.show()
    map.save('test.png')
    