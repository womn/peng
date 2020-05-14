import ctypes
import sys

class setcolor(object):
    def __init__(self):
        self.STD_INPUT_HANDLE = -10
        self.STD_OUTPUT_HANDLE = -11
        self.STD_ERROR_HANDLE = -12

        #字体颜色定义 text colors
        self.FOREGROUND_BLUE = 0x09 # blue.
        self.FOREGROUND_GREEN = 0x0a # green.
        self.FOREGROUND_RED = 0x0c # red.
        self.FOREGROUND_YELLOW = 0x0e # yellow.

        # get handle
        self.std_out_handle = ctypes.windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)
 
    def set_cmd_text_color(self, color):
        Bool = ctypes.windll.kernel32.SetConsoleTextAttribute(self.std_out_handle, color)
        return Bool
    
    #reset white
    def resetColor(self):
        self.set_cmd_text_color(self.FOREGROUND_RED | self.FOREGROUND_GREEN | self.FOREGROUND_BLUE)
    
    #green
    def setPrintGreen(self):
        self.set_cmd_text_color(self.FOREGROUND_GREEN)

    #red
    def setPrintRed(self):
        self.set_cmd_text_color(self.FOREGROUND_RED)
        
