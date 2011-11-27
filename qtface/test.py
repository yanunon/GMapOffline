#!/usr/bin/env python
#-*- coding:utf-8 -*-
'''
Created on 2011-11-14

@author: "Yang Junyong <yanunon@gmail.com>"
'''
import sys
import time

from PyQt4 import QtCore, QtGui

class Example(QtGui.QWidget):
    def __init__(self):
        super(Example, self).__init__()
        self.initUI()
    
    def initUI(self):
        lcd = QtGui.QLCDNumber(self)
        sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        button = QtGui.QPushButton('Dialog', self)
        button.clicked.connect(self.showDialog)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(lcd)
        vbox.addWidget(sld)
        vbox.addWidget(button)
        
        self.setLayout(vbox)
        sld.valueChanged.connect(lcd.display)
        color = QtGui.QColor(0,0,0)
        self.frm = QtGui.QFrame(self)
        self.frm.setStyleSheet("QWidget { background-color: %s}" % color.name())
        self.frm.setGeometry(0,0,100,100)
        
        self.setGeometry(300,300,250,200)
        self.show()
    
    def showDialog(self):
        
        fname = QtGui.QFileDialog.getOpenFileName(self,"Folder","/home")
        print fname
        
    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'MessageBox', 'Are you sure to quit?', buttons=QtGui.QMessageBox.Yes|QtGui.QMessageBox.No, defaultButton=QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

def main():
    app = QtGui.QApplication(sys.argv)
    e = Example()
    sys.exit(app.exec_()) 
        
if __name__ == '__main__':
    main()
            
    