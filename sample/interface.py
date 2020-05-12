import sys,math
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
import requests
import csv
import os
import getpass  # 获取host
import datetime
import pandas as pd
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


class MainWindow(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("产测")
        self.resize(540, 640)
        self.setMinimumSize(QSize(540, 640))
        self.setStyleSheet("background-color: rgb(255, 255, 255)")
        # 信道板产测
        self.nchpproduce = QPushButton(self)
        self.nchpproduce.setGeometry(QRect(0, 555, 90, 27))
        self.nchpproduce.setObjectName("nchpproduce")

        # 信道板老化
        self.nchpoldproduce = QPushButton(self)
        self.nchpoldproduce.setGeometry(QRect(80, 555, 90, 27))
        self.nchpoldproduce.setObjectName("nchpoldproduce")

        # 整机产测
        self.allproduce = QPushButton(self)
        self.allproduce.setGeometry(QRect(160, 555, 90, 27))
        self.allproduce.setObjectName("allproduce")

        # MX2080整机产测
        self.allproduce_mx2080 = QPushButton(self)
        self.allproduce_mx2080.setGeometry(QRect(240, 555, 240, 27))
        self.allproduce_mx2080.setObjectName("allproduce_mx2080")

        # 整机功率校准
        self.dpow = QPushButton(self)
        self.dpow.setGeometry(QRect(320, 555, 90, 27))
        self.dpow.setObjectName("dpow")

        self.nchpproduce.setText("信道板产测")
        self.nchpoldproduce.setText("信道板老化")
        self.allproduce.setText("整机产测")
        self.allproduce_mx2080.setText("MX2080整机产测")
        self.dpow.setText("整机功率校准")

        # 按钮的连接
        self.nchpproduce.clicked.connect(self.shownchpproduce)
        self.nchpoldproduce.clicked.connect(self.shownchpoldproduce)
        self.allproduce.clicked.connect(self.showallproduce)
        self.allproduce_mx2080.clicked.connect(self.showallproduce_mx2080)
        self.dpow.clicked.connect(self.showdpow)

        self.shownchpproduce()
    def shownchpproduce(self):
        print("nchpproduce")
    def shownchpoldproduce(self):
        print("shownchpoldproduce")
    def showallproduce(self):
        print("showallproduce")
    def showallproduce_mx2080(self):
        print("showallproduce_mx2080")
    def showdpow(self):
        print("showdpow")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())