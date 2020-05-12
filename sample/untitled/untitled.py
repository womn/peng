# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'untitled.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets






class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 23))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menucaidan = QtWidgets.QMenu(self.menubar)
        self.menucaidan.setObjectName("menucaidan")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action1 = QtWidgets.QAction(MainWindow)
        self.action1.setObjectName("action1")
        self.action2 = QtWidgets.QAction(MainWindow)
        self.action2.setObjectName("action2")
        self.action3 = QtWidgets.QAction(MainWindow)
        self.action3.setObjectName("action3")
        self.action4 = QtWidgets.QAction(MainWindow)
        self.action4.setObjectName("action4")
        self.action4_2 = QtWidgets.QAction(MainWindow)
        self.action4_2.setObjectName("action4_2")
        self.actionfdsf = QtWidgets.QAction(MainWindow)
        self.actionfdsf.setObjectName("actionfdsf")
        self.menu.addAction(self.actionfdsf)
        self.menucaidan.addAction(self.action1)
        self.menucaidan.addAction(self.action2)
        self.menucaidan.addAction(self.action3)
        self.menucaidan.addAction(self.action4)
        self.menucaidan.addAction(self.action4_2)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menucaidan.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.menu.setTitle(_translate("MainWindow", "文件"))
        self.menucaidan.setTitle(_translate("MainWindow", "菜单"))
        self.action1.setText(_translate("MainWindow", "1"))
        self.action2.setText(_translate("MainWindow", "2"))
        self.action3.setText(_translate("MainWindow", "3"))
        self.action4.setText(_translate("MainWindow", "4"))
        self.action4_2.setText(_translate("MainWindow", "5"))
        self.actionfdsf.setText(_translate("MainWindow", "fdsf"))
