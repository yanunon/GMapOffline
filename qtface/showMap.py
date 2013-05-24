#!/usr/bin/env python
#-*- coding:utf-8 -*-
'''
Created on 2011-11-15

@author: "Yang Junyong <yanunon@gmail.com>"
'''

import sys
import os
from PyQt4 import QtCore,QtGui

import gmaps.mapDownloader as mapDownloader
from gmaps.mapTool import coord_to_tile

class Example(QtGui.QWidget):
    def __init__(self):
        super(Example, self).__init__()
        self.initUI()
        self.center = [39.94,116.38]
        self.zoom = 9
        self.layer = 'mixed_cn'
        self.downloader = mapDownloader.MapDownloader(10)
        self.window_size = [511, 511]
        self.half_window_size = (self.window_size[0]/2, self.window_size[1]/2)
        self.xmin = -100
        self.xmax = -100
        self.ymin = -100
        self.ymax = -100
        self.need_fresh = False
        
        self.do_download()
        
        
    def initUI(self):
        self.label = QtGui.QLabel()
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.label)
        
        self.setLayout(vbox)
        
        self.setGeometry(100,100,550,550)
        self.show()
        
    def do_download(self):
        tile = coord_to_tile((self.center[0],self.center[1],self.zoom))
        x_count = ((self.half_window_size[0] + 255)/256 ) * 2 + 1
        y_count = ((self.half_window_size[1] + 255)/256 ) * 2 + 1
        
        xmin = tile[0][0] - x_count/2
        xmax = xmin + x_count
        
        ymin = tile[0][1] - y_count/2
        ymax = ymin + y_count
        
        
        
        self.map_top_left_point = (self.half_window_size[0] - x_count/2*256 - tile[1][0], self.half_window_size[1] - y_count/2*256 - tile[1][1])
        #self.map_top_left_point = (0,0)
        print self.map_top_left_point[0],self.map_top_left_point[1]
        
        if self.xmin != xmin or self.xmax != xmax or self.ymin != ymin or self.ymax != ymax:
            self.xmin = xmin
            self.xmax = xmax
            self.ymin = ymin
            self.ymax = ymax
            self.downloader.dl_region(self.xmin - 1, self.xmax + 1, self.ymin - 1 , self.ymax + 1, self.zoom, self.layer)
            #self.downloader.wait_thread_done()
            #self.downloader.wait()
            #print 'download over!'
            self.refresh_map()
        #self.map_qpiximage.save("test.jpg")
        #print self.map_top_left_point
        
        #self.update()
        
    def paintEvent(self, event):
        ui_painter = QtGui.QPainter(self)
        ui_painter.drawPixmap(QtCore.QRect(10,10,self.window_size[0],self.window_size[1]),
                              self.map_qpiximage, 
                              QtCore.QRect(-self.map_top_left_point[0],-self.map_top_left_point[1],self.window_size[0],self.window_size[1]))
        
    def keyPressEvent(self, event):
        #print event.key()
        #print QtCore.Qt.Key_Right
        key_list = [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Down, QtCore.Qt.Key_Up, QtCore.Qt.Key_Plus, QtCore.Qt.Key_Minus]
        keyboard = event.key()
        if keyboard == QtCore.Qt.Key_Escape:
            self.close()
        elif keyboard in key_list:
            factor = 10.0 / (1 << self.zoom)
            if keyboard == QtCore.Qt.Key_Left:
                self.center[1] += factor
            elif keyboard == QtCore.Qt.Key_Right:
                self.center[1] -= factor
            elif keyboard == QtCore.Qt.Key_Up:
                self.center[0] -= factor
            elif keyboard == QtCore.Qt.Key_Down:
                self.center[0] += factor
            elif keyboard == QtCore.Qt.Key_Plus:
                self.zoom += 1
            elif keyboard == QtCore.Qt.Key_Minus:
                self.zoom -= 1
                    
            if self.zoom > 17:
                self.zoom = 17
            elif self.zoom < 0:
                self.zoom = 0
            
            self.do_download()
            self.update()
            if self.need_fresh:
                self.refresh_map()
    
    def closeEvent(self, event):
        self.downloader.wait_and_stop()
    
    def refresh_map(self):
        x_count = self.xmax - self.xmin + 1
        y_count = self.ymax - self.ymin + 1
        self.need_fresh = False
        self.map_qpiximage = QtGui.QPixmap(x_count*256, y_count*256)
        merge_painter = QtGui.QPainter(self.map_qpiximage)
        #temp_pix = QtGui.QPixmap(256,256)
        for x in range(x_count + 1):
            for y in range(y_count + 1):
                tile = mapDownloader.MapTile(self.layer, self.xmin + x, self.ymin + y, self.zoom)
                file_path = tile.get_file_path()
                temp_pix = QtGui.QPixmap(file_path)
                if temp_pix.isNull():
                    self.need_fresh = True
                else:
                    merge_painter.drawPixmap(QtCore.QRect(x*256,y*256,256,256), temp_pix, QtCore.QRect(0,0,256,256))
        
def main():
    app = QtGui.QApplication(sys.argv)
    #temp_pix = QtGui.QPixmap('test.jpg')
    #print temp_pix.isNull()
    e = Example()
    #e.show()
    sys.exit(app.exec_()) 
        
if __name__ == '__main__':
    
    main()

