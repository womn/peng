# -*-coding:utf-8-*-
from PyQt5 import QtCore, QtGui, QtWidgets
import sys,math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import configparser 
import gbthread, setcolor, translation

def LoggerInit(file_name):

    # debug
    # if True:
    if False:
        level = logging.DEBUG
        logger = logging.getLogger(__name__)

        fh = logging.FileHandler(file_name)
        fh.setLevel(level)

        logging.basicConfig(level = level, format = '-- %(filename)s:%(funcName)s():%(lineno)d %(levelname)s:   %(message)s')
        logger.addHandler(fh)
    else:
        level = logging.INFO
        logger = logging.getLogger(__name__)

        fh = logging.FileHandler(file_name)
        fh.setLevel(level)
        logging.basicConfig(level = level, format = '-- %(levelname)s:   %(message)s')
        logger.addHandler(fh)
    
    return fh, logger

def dpowrun(self,mainwindow):
    QMessageBox.about(mainwindow, "整机功率校准", "生产开始啦")
    file_name = "-log.txt"
    log_file = mac + file_name
    fh, logger = LoggerInit(log_file)

    translation = translation()
    zh_cn = translation.GetTranslation

    logger.info(log_file)
    path = os.getcwd() + "\\file"
    
    work_thread = gbthread(cfg, logger, zh_cn, fh, col, mac, path)
    work_thread.start()

