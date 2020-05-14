import time
import _thread
import sys
import paramiko
import os
import operator

class connect(object):
    def __init__(self, cfg, logger, ping_thread, language, col, path):
        self.__cfg = cfg
        self.__logger = logger
        self.__zh_cn = language
        self.__col = col
        self.__path = path

        self.__ping_thread = ping_thread
        
        self.__mcb_username = self.__cfg.get("dut", "username")
        self.__mcb_password = self.__cfg.get("dut", "password")
        self.__mcb_password2 = self.__cfg.get("dut", "password2")
        self.__dut_ip = self.__cfg.get("dut", "dev_ip")
        self.__dut_local_ip = self.__cfg.get("dut", "local_ip")
        self.__dut_port = self.__cfg.get("dut", "ssh_port")
        self.__scp_pathname = self.__path

        # 连接失败时尝试连接次数
        self.telnethost_times = 5

        # ping失败时尝试次数
        self.connect_ping_test_times = 5
        self.connect_succ_sleep = 0.2
        self.connect_fail_sleep = 0.2
        
        self.TelnetLock = _thread.allocate_lock()
        self.ssh_client = {}

    def TestConnect(self, ip):
        if self.__ping_thread.PingManyTimes(ip, 5) == False:
            self.__logger.error(self.__zh_cn("check_fail"))
            return False
        return True

    def SSHClient(self, ip, port, username, password):
        self.__logger.info(self.__zh_cn("start_connect_ssh"), ip, port)
        
        for i in range(self.telnethost_times):
            try:
                self.TelnetLock.acquire()

                # ssh
                self.ssh_client[ip] = paramiko.SSHClient()
                self.ssh_client[ip].set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client[ip].connect(hostname=ip, port=22, username=username, password=password, \
                    timeout=10, banner_timeout=10, auth_timeout=10)
                    
                self.TelnetLock.release()

                self.__logger.info(self.__zh_cn("check_success"))

                return

            except Exception as e:
                if i == self.telnethost_times - 1:
                    if not self.TestConnect(ip):
                        self.__col.setPrintRed()
                        self.__logger.error(self.__zh_cn("connect_break"))
                        self.__col.resetColor()
                        sys.exit(-1)
                    else:
                        self.__col.setPrintRed()
                        self.__logger.error(self.__zh_cn("check_fail") + str(e))
                        self.__col.resetColor()

    def SSHExecCmdUntil(self, ip, cmd, dut_str, exit_str="", timeout=180):
        line = False
        exec_time = time.time()

        try:
            self.TelnetLock.acquire()
            # print(cmd)

            # 传输命令，这里有三个返回值，按顺序第一个是标准输入，即你输入的命令，第二个标准输出，即命令返回值
            # 第三个标准错误，报错的时候会返回给这个值，同时返回值不是固
            # 定而是变化的时候也会返回给这个值一个错误
            stdin, stdout, stderr = self.ssh_client[ip].exec_command(cmd, get_pty=True, timeout = 120.0)

            self.TelnetLock.release()

        except Exception as e:
            if not self.TestConnect(ip):
                self.__col.setPrintRed()
                self.__logger.error(self.__zh_cn("connect_break"))
                self.__col.resetColor()
                sys.exit(-1)
            else:
                self.__col.setPrintRed()
                self.__logger.error(self.__zh_cn("connect_fail") + str(e))
                self.__col.resetColor()
                sys.exit(-1)

        while True:
            try:
                res = stdout.readline().splitlines()
                # print(res)
                if len(res) != 0:
                    exec_time = time.time()
                    
                    line = res[0]
                    self.__logger.debug(line)
                    print(line)

                    if line.find(dut_str) >= 0:
                        break

                    if not operator.eq(exit_str, "") and line.find(exit_str) >= 0:
                        return False
                else:
                    # 防止卡死
                    if time.time() - exec_time > timeout:
                        self.__logger.error(self.__zh_cn("read_line_timeout"))
                        return False

            except Exception as e:
                break

        return line

    def SSHInvokeShellInit(self, ip):
        chan = self.ssh_client[ip].invoke_shell()

        # 尝试执行命令看是否要输入二级密码（不用版本需要输入密码）
        ret = self.SSHInvokeShell(chan, "ls")
        if "password" in ret:
            # 输入二级密码
            self.SSHInvokeShell(chan, self.__mcb_password2)

        return chan

    def SSHInvokeShellClose(self, chan):
        chan.close()

    def SSHInvokeShell(self, chan, cmd, timeout=0.5):
        chan.send(cmd + '\n')
        time.sleep(timeout)
        ret = chan.recv(1024)
        return ret.decode("utf-8")

    def SSHInvokeShellUntil(self, chan, cmd, dut_str, timeout=1):
        chan.send(cmd + '\n')
        while True:
            time.sleep(timeout)
            ret = chan.recv(1024)
            ret = ret.decode("utf-8")
            print(ret)
            if dut_str in ret:
                break
        return ret

    def SSHExecCmd(self, ip, cmd, get_pty=True):
        try:
            self.TelnetLock.acquire()
            # print(cmd)

            # 传输命令，这里有三个返回值，按顺序第一个是标准输入，即你输入的命令，第二个标准输出，即命令返回值
            # 第三个标准错误，报错的时候会返回给这个值，同时返回值不是固
            # 定而是变化的时候也会返回给这个值一个错误
            stdin, stdout, stderr = self.ssh_client[ip].exec_command(cmd, get_pty=get_pty)

            self.TelnetLock.release()

            res = stdout.readline().splitlines()
            if len(res) != 0:
                return res[0]

            self.__logger.debug(res)
            # print(res)

            return res

        except Exception as e:
            print("err" + str(e))
            if not self.TestConnect(ip):
                self.__col.setPrintRed()
                self.__logger.error(self.__zh_cn("connect_break"))
                self.__col.resetColor()
                sys.exit(-1)
            else:
                self.__col.setPrintRed()
                self.__logger.error(self.__zh_cn("connect_fail") + str(e))
                self.__col.resetColor()
                sys.exit(-1)

    def SSHClose(self, ip):
        self.ssh_client[ip].close()
        self.ssh_client[ip] = None

    def tryPing(self, ip):
        # 尝试PING通设备
        ping_fail_time = 0
        while self.__ping_thread.PingManyTimes(ip, 1) == False:
            ping_fail_time = ping_fail_time + 1
            time.sleep(self.connect_fail_sleep)

            if ping_fail_time >= self.connect_ping_test_times:
                self.__col.setPrintRed()
                self.__logger.error(self.__zh_cn("ping_fail"))
                self.__col.resetColor()
                return False

        return True

    def ConnectBoard(self):
        # ping主控板
        if True == self.tryPing(self.__dut_ip):
            # ssh连接主控板
            self.SSHClient(self.__dut_ip, self.__dut_port, self.__mcb_username, self.__mcb_password)
            # 输入二级密码
            # self.SSHExecCmd(self.__dut_ip, "GW-ieee802.11")

            # Ping信道板并建立ssh连接
            # for ip in self.__nchp_ip:
            #     if True == self.tryPing(ip):
            #         self.SSHClient(ip, self.__ssh_port, self.__nchp_username, self.__nchp_password)
            #     else:
            #         sys.exit(-1)

            return True

    def getData(self, filed):
        if operator.eq(filed, "dut_ip"):
            return self.__dut_ip
        if operator.eq(filed, "dut_port"):
            return self.__dut_port
        # elif operator.eq(filed, "nchp_ip"):
        #     return self.__nchp_ip
        # elif operator.eq(filed, "ssh_port"):
        #     return self.__ssh_port
        # elif operator.eq(filed, "nchp_username"):
        #     return self.__nchp_username
        # elif operator.eq(filed, "nchp_password"):
        #     return self.__nchp_password
        elif operator.eq(filed, "mcb_username"):
            return self.__mcb_username
        elif operator.eq(filed, "mcb_password"):
            return self.__mcb_password
        elif operator.eq(filed, "mcb_password2"):
            return self.__mcb_password2
        elif operator.eq(filed, "local_ip"):
            return self.__dut_local_ip

    def upload_file(self, ip, name, remote_path="/tmp"):
        sftp = paramiko.SFTPClient.from_transport(self.ssh_client[ip].get_transport())
        sftp = self.ssh_client[ip].open_sftp()

        local_path = self.__scp_pathname + "\\" + name

        self.__logger.debug("local_path: " + local_path)
        self.__logger.debug("remote_path: " + remote_path)
        try:
            sftp.put(local_path, remote_path)
        except Exception as e:
            print(e)
            
