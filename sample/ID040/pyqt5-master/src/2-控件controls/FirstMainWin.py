import sys
from PyQt5.QtWidgets import QMainWindow,QApplication
from PyQt5.QtGui import QIcon

class FirstMainWin(QMainWindow):
    def __init__(self):
        super(FirstMainWin,self).__init__() #继承父类的初始化后并且需要添加或者更改自己的一些初始化设置
        self.setWindowTitle('第一个主窗口应用') # 设置主窗口的标题
        self.resize(400,300)  # 设置窗口的尺寸
        self.status = self.statusBar()  #创建状态栏
        #状态栏显示消息
        self.status.showMessage('只存在5秒的消息',5000)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    #窗口图标，单独运行时注意运行目录
    app.setWindowIcon(QIcon('./images/Dragon.ico'))
    main = FirstMainWin()
    main.show()

    sys.exit(app.exec_())