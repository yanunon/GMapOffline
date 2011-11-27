#!/usr/bin/env python
#-*- coding:utf-8 -*-
'''
Created on 2011-11-13

@author: "Yang Junyong <yanunon@gmail.com>"
'''

import os
import Image
import mapTool


FILE_TYPE = {
             'gmap' : 'png',
             'gsat' : 'jpeg',
             'ghyb' : 'jpeg',
             'gter' : 'jpeg'
             }


data_folder = '/home/kite/work/python/workspace/GMapKinect/mapdata'

def save_map_file(file_data, x, y, z, layer, overwrite=False):
    
    folder_path, file_path = get_tile_path(layer, x, y, z)
    
    if not overwrite and os.path.exists(file_path):
        return
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    try:
        file = open(file_path, 'wb')
        file.write(file_data)
        file.close()
    except Exception,e:
        #logging.info("Writing file:%s failed! Msg:%s" %(file_path, str(e)))
        print ("Writing file:%s failed! Msg:%s" %(file_path, str(e)))
    #else:
        #logging.info("Writing file:%s successed!" %(file_path))
        #print ("Writing file:%s successed!" %(file_path))
        
        
def get_tile_path(layer, x, y, z):
    world_tile = 1 << z
    x = x % world_tile
    folder_list = [layer, z, x/1024, x%1024, y/1024]
    file_name = "%d.%s" % (y%1024 , FILE_TYPE[layer])
    folder_path = data_folder
    for sub in folder_list:
        folder_path = os.path.join(folder_path, str(sub))
    file_path = os.path.join(folder_path, file_name)
    return folder_path,file_path

def merge_region_image(xmin, xmax, ymin, ymax, zoom, layer):
    world_tiles = 1 << zoom
    if xmax - xmin >= world_tiles:
        xmin, xmax = 0, world_tiles-1
    if ymax - ymin >= world_tiles:
        ymin, ymax = 0, world_tiles-1
    width = (xmax - xmin+world_tiles)%world_tiles
    height = (ymax - ymin+world_tiles)%world_tiles
    map_image = Image.new("RGB", (width*256,height*256))
    for i in xrange(width):
        x = (xmin + i)%world_tiles
        for j in xrange(height):
            y = (ymin + j)%world_tiles
            file_path = get_tile_path(layer, x, y, zoom)[1]
            if os.path.exists(file_path):
                paste_box = (i*256, j*256, (i+1)*256, (j+1)*256)
                paste_im = Image.open(file_path)
                map_image.paste(paste_im, paste_box)
    return map_image

def merge_location_image(top_left, bottom_right, zoom, layer):
    top_left_tile = mapTool.coord_to_tile((top_left[0], top_left[1], zoom))
    bottom_right_tile = mapTool.coord_to_tile((bottom_right[0], bottom_right[1], zoom))
    
    xmin = top_left_tile[0][0]
    ymin = top_left_tile[0][1]
    
    xmax = bottom_right_tile[0][0]
    ymax = bottom_right_tile[0][1]
    return merge_region_image(xmin, xmax, ymin, ymax, zoom, layer)

if __name__ == '__main__':
    #save_map_file('111', 10, 10, 10, 'gmap', True)
    #print os.path.dirname(__file__)
    pass