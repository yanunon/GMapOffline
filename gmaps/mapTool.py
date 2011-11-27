#!/usr/bin/env python
#-*- coding:utf-8 -*-
'''
Created on 2011-11-12

@author: "Yang Junyong <yanunon@gmail.com>"
'''

import math


def coord_to_tile(coord):
    world_tiles = 1 << coord[2]
    x = world_tiles / 360.0 * (coord[1] + 180.0)
    tiles_pre_radian = world_tiles / (2 * math.pi)
    e = math.sin(coord[0] * (1/180.*math.pi))
    y = world_tiles/2 + 0.5*math.log((1+e)/(1-e)) * (-tiles_pre_radian)
    offset = int((x - int(x)) * 256), \
             int((y - int(y)) * 256)
    return (int(x) % world_tiles, int(y) % world_tiles), offset

def tile_to_coord(tile, zoom):
    world_tiles = 1 << int(zoom)
    x = ( tile[0][0] + 1.0*tile[1][0]/256 ) / (world_tiles/2.) - 1 # -1...1
    y = ( tile[0][1] + 1.0*tile[1][1]/256) / (world_tiles/2.) - 1 # -1...1
    lon = x * 180.0
    y = math.exp(-y*2*math.pi)
    e = (y-1)/(y+1)
    lat = 180.0/math.pi * math.asin(e)
    return lat, lon, zoom


if __name__ == '__main__':
    pass