#!/usr/bin/env python
#-*- coding:utf-8 -*-
'''
Created on 2013-5-23

@author: "Yang Junyong <yanunon@gmail.com>"
'''
import sqlite3
import os
import mapDownloader
import datetime

TABLE_DDL = "CREATE TABLE IF NOT EXISTS tiles (x int, y int, z int, s int, image blob, PRIMARY KEY (x,y,z,s))"
INDEX_DDL = "CREATE INDEX IF NOT EXISTS IND on tiles (x,y,z,s)"
INSERT_SQL = "INSERT or REPLACE INTO tiles (x,y,z,s,image) VALUES (?,?,?,0,?)"
RMAPS_TABLE_INFO_DDL = "CREATE TABLE IF NOT EXISTS info AS SELECT 99 AS minzoom, 0 AS maxzoom"
RMAPS_CLEAR_INFO_SQL = "DELETE FROM info;"
RMAPS_UPDATE_INFO_MINMAX_SQL = "INSERT INTO info (minzoom,maxzoom) VALUES (?,?);"
RMAPS_INFO_MAX_SQL = "SELECT DISTINCT z FROM tiles ORDER BY z DESC LIMIT 1;"
RMAPS_INFO_MIN_SQL = "SELECT DISTINCT z FROM tiles ORDER BY z ASC LIMIT 1;"

class MapSqlite(object):
    def __init__(self):
        self.downloader = mapDownloader.MapDownloader(10)
    
    def open_db(self, name):
        self.conn = sqlite3.connect(name)
        self.__create_table()  
        
    def __create_table(self):
        #create android_metadata table
        cur = self.conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS android_metadata (locale TEXT)')
        cur.execute('SELECT * FROM android_metadata')
        if len(cur.fetchall()) == 0:
            cur.execute('INSERT INTO android_metadata VALUES ("zh_CN")')
            self.conn.commit()
 
        #create tiles table
        cur.execute(TABLE_DDL)
        cur.execute(INDEX_DDL)
        
        #create info table
        cur.execute(RMAPS_TABLE_INFO_DDL)
        cur.execute(RMAPS_CLEAR_INFO_SQL)
        self.conn.commit()
        cur.close()
 
    def __insert_tile(self, tile):
        
        tile_path = tile.get_file_path()
        if os.path.exists(tile_path):
            imgf = open(tile_path, 'rb')
            img = imgf.read()
            imgf.close()
        
            cur = self.conn.cursor()
            cur.execute(INSERT_SQL, (tile.x, tile.y, 17 - tile.z, sqlite3.Binary(img)))
            self.conn.commit()
            cur.close()
            
    def __insert_tiles(self, tiles):
        to_insert = []
        cur = self.conn.cursor()
        for tile in tiles:
            tile_path = tile.get_file_path()
            if os.path.exists(tile_path):
                imgf = open(tile_path, 'rb')
                img = imgf.read()
                imgf.close()
                to_insert.append((tile.x, tile.y, 17 - tile.z, sqlite3.Binary(img)))
                
                if len(to_insert) == 20:
                    cur.executemany(INSERT_SQL, to_insert)
                    self.conn.commit()
                    to_insert = []
                    
        cur.executemany(INSERT_SQL, to_insert)
        self.conn.commit()
        cur.close()
 
    def __update_info(self):
        cur = self.conn.cursor()
        
        cur.execute(RMAPS_CLEAR_INFO_SQL)
        self.conn.commit()
        
        cur.execute(RMAPS_INFO_MAX_SQL)
        max_result = cur.fetchone()
        cur.execute(RMAPS_INFO_MIN_SQL)
        min_result = cur.fetchone()
        if max_result and min_result:
            max_res = max_result[0]
            min_res = min_result[0]
            cur.execute(RMAPS_UPDATE_INFO_MINMAX_SQL, (min_res, max_res))
            self.conn.commit()
        cur.close()
 
    def close_db(self):
        self.conn.close()
        
    def download(self, top_left, bottom_right, zooms, layer):
        for z in range(zooms[0], zooms[1]):
            self.downloader.dl_location(top_left, bottom_right, z, layer)
        self.downloader.wait_thread_done()
        print 'download from internet over...'
        print 'insert to database...'
        start = datetime.datetime.now()
        for z in range(zooms[0], zooms[1]):
            tiles = mapDownloader.get_location_tiles(top_left, bottom_right, z, layer)
            self.__insert_tiles(tiles)
            self.__update_info()
        end = datetime.datetime.now()
        used = end - start
        print used.total_seconds()
        
if __name__ == '__main__':
    top_left = (39.976462,116.3337)
    bottom_right = (39.949359,116.379963)
    layer = 'mixed_cn'
    zooms = [0, 18]
    map = MapSqlite()
    map.open_db('test.sqlitedb')
    map.download(top_left, bottom_right, zooms, layer)
    map.close_db()