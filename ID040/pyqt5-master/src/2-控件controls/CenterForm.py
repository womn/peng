# QDesktopWidget
import sys
from PyQt5.QtWidgets import QDesktopWidget,QMainWindow,QApplication
from PyQt5.QtGui import QIcon

class CenterForm(QMainWindow):
    def __init__(self):
        super(CenterForm,self).__init__()
        self.setWindowTitle('让窗口居中') # 设置主窗口的标题
        self.resize(400,300) # 设置窗口的尺寸

    def center(self):
        screen = QDesktopWidget().screenGeometry() # 获取屏幕坐标系
        size = self.geometry() # 获取窗口坐标系
        newLeft = (screen.width() - size.width()) / 2
        newTop = (screen.height() - size.height()) / 2
        print(newLeft)
        print(newTop)
        self.move(newLeft,newTop)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = CenterForm()
    main.show()

    sys.exit(app.exec_())
