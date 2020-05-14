import threading
import socket
import sys
import os
import time
import tftpy

class tftp(threading.Thread):
    def __init__(self, cfg, logger, language, path):
        threading.Thread.__init__(self)
        self.__cfg = cfg
        self.__logger = logger
        self.__zh_cn = language
        self.__path = path

        self.port = 69

        # 检查tftp端口
        while self.CheckTftpPort(self.port) == False:
            time.sleep(1)
            continue
        
        # 检查tftp目录
        self.ChceckServerPath()

        self.setDaemon(True)

    def CheckTftpPort(self, port):
        sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 通过socket判断端口是否已经被占用
            sock.bind(('0.0.0.0', port))
        except:
            self.__logger.info(self.__zh_cn("tftp_port_occupied"))
            sock.close()
            return False
        
        sock.close()
        return True

    def ChceckServerPath(self):
        if not os.path.isdir(self.__path):
            self.__logger.error(self.__zh_cn("tftp_lack_path") + self.__path)
            sys.exit(-1)

    def run(self):
        self.__tftp_server = tftpy.TftpServer(self.__path)
        self.__logger.info(self.__zh_cn("tftp_success"), self.__path)
        self.__tftp_server.listen("0.0.0.0", self.port)
