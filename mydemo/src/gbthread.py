import threading
import time
import os
import operator
import sys

from .ping import PingNetwork
from .common import common
from .tftp import tftp

class gbthread(threading.Thread):
    def __init__(self, cfg, logger, language, fh, col, mac, path):
        threading.Thread.__init__(self)

        self.__logger = logger
        self.__zh_cn = language
        self.__fh = fh
        self.__col = col
        self.__mac = mac
        self.__path = path

        self.__test_step_order = self.__cfg.get("test_step", "step_order")
        self.__manual_test_item_list = self.__cfg.get(
            "manual_test_item", "item").strip().split(',')

        self.ping_thread = PingNetwork(self.__cfg, self.__logger, self.__zh_cn)
        self.plat = common(self.__cfg, self.__logger,
                           self.ping_thread, self.__zh_cn, self.__col, self.__path)
        self.finish_status = 0

        # 启动tftp服务器线程
        self.tftp = tftp(self.__cfg, self.__logger, self.__zh_cn, self.__path)
        # self.tftp.start()
        self.start_time = int(time.time())

        self.setDaemon(True)

    def run(self):
        self.__logger.info(self.__zh_cn("start"))
        if True == self.plat.ConnectBoard():
            self.MainRun(self.plat.getData("dut_ip"))
        else:
            sys.exit(-1)

    def ExecTest(self, dut_ip):
        # 手动测试
        if operator.eq(self.__test_step_order, "ManualTest"):
            for test_item in self.__manual_test_item_list:
                if test_item in self.plat.GetSupportTestItem():
                    self.plat.DoTest(test_item, dut_ip)
                else:
                    self.__logger.warn(self.__zh_cn("dont_support_item") + test_item)
        # 自动测试
        elif operator.eq(self.__test_step_order, "AutoTest"):
            # 记录测试到哪一步
            tmp_path = self.__path + "\\..\\log\\"
            if not os.path.exists(tmp_path):
                os.mkdir(tmp_path)
            tmp_path = self.__path + "\\..\\log\\tmp\\"
            if not os.path.exists(tmp_path):
                os.mkdir(tmp_path)

            step_tmp = tmp_path + self.getLogNmae() + ".step"

            if os.path.exists(step_tmp):
                # 测试通过则跳过
                # ret = input(self.__zh_cn("testd_fail"))
                # if "y" in ret or "Y" in ret:
                #     os.remove(step_tmp)
                os.remove(step_tmp)

            step_fd = open(step_tmp, "a+")
            step_fd.seek(0)
            step_content = step_fd.read()
            step_fd.close()

            for test_item in self.plat.GetSupportTestItem():
                if test_item in step_content:
                    self.__logger.info(self.__zh_cn(
                        test_item) + self.__zh_cn("testd"))
                    continue

                if True == self.plat.DoTest(test_item, dut_ip):
                    step_fd = open(step_tmp, "a+")
                    step_fd.write(test_item + "\n")
                    step_fd.close()
                # quit when you fail
                else:
                    break

            self.finish_status = 1

    def CollectResult(self, col, exit_int=0):
        if exit_int == 1:
            self.plat.test_fail_item["test_not_finish"] = "interrput exit"
            if self.finish_status == 1:
                return

        # 打印所有结果
        self.__logger.info(self.__zh_cn("start_collect_result"))
        for key in list(self.plat.test_success_item_result.keys()):
            if (operator.eq(self.plat.test_success_item_result[key], self.__zh_cn("check_fail"))):
                col.setPrintRed()
            elif (operator.eq(self.plat.test_success_item_result[key], self.__zh_cn("check_success"))):
                col.setPrintGreen()
            self.__logger.info(
                "%s : %s", key, self.plat.test_success_item_result[key])
        col.resetColor()

        if len(self.plat.test_fail_item) > 0:
            # 打印测试失败的项目
            col.setPrintRed()
            self.__logger.info(self.__zh_cn("start_collect_fail_item"))
            for key in list(self.plat.test_fail_item.keys()):
                self.__logger.info(
                    "%s : %s", key, self.plat.test_fail_item[key])
            self.__logger.info(self.__zh_cn("end_collect_result"))

            self.__logger.error(
                "   #######################################################################")
            self.__logger.error(
                "   ##                                                                   ##")
            self.__logger.error(
                "   ##                    ########    ###     ####  ##                   ##")
            self.__logger.error(
                "   ##                    ##         ## ##     ##   ##                   ##")
            self.__logger.error(
                "   ##                    ##        ##   ##    ##   ##                   ##")
            self.__logger.error(
                "   ##                    ######   ##     ##   ##   ##                   ##")
            self.__logger.error(
                "   ##                    ##       #########   ##   ##                   ##")
            self.__logger.error(
                "   ##                    ##       ##     ##   ##   ##                   ##")
            self.__logger.error(
                "   ##                    ##       ##     ##  ####  ########             ##")
            self.__logger.error(
                "   ##                                                                   ##")
            self.__logger.error(
                "   #######################################################################")

            col.resetColor()
        else:
            self.__logger.info(self.__zh_cn("end_collect_result"))
            col.setPrintGreen()
            self.__logger.info(
                "   #######################################################################")
            self.__logger.info(
                "   ##                                                                   ##")
            self.__logger.info(
                "   ##                 ########     ###     ######   ######              ##")
            self.__logger.info(
                "   ##                 ##     ##   ## ##   ##    ## ##    ##             ##")
            self.__logger.info(
                "   ##                 ##     ##  ##   ##  ##       ##                   ##")
            self.__logger.info(
                "   ##                 ########  ##     ##  ######   ######              ##")
            self.__logger.info(
                "   ##                 ##        #########       ##       ##             ##")
            self.__logger.info(
                "   ##                 ##        ##     ## ##    ## ##    ##             ##")
            self.__logger.info(
                "   ##                 ##        ##     ##  ######   ######              ##")
            self.__logger.info(
                "   ##                                                                   ##")
            self.__logger.info(
                "   #######################################################################")
            col.resetColor()

        # 重命名log文件
        log_pathname = self.__path + "\\..\\" + self.__mac + "-log.txt"

        fail_path = self.__path + "\\..\\log\\fail\\"
        success_path = self.__path + "\\..\\log\\success\\"

        if not os.path.exists(self.__path):
            os.mkdir(self.__path)
        if not os.path.exists(fail_path):
            os.mkdir(fail_path)
        if not os.path.exists(success_path):
            os.mkdir(success_path)

        # 计算用时
        end_time = int(time.time())
        m, s = divmod(end_time-self.start_time, 60)
        self.__logger.info(self.__zh_cn("used_time") + "%02d:%02d" % (m, s))

        if len(self.plat.test_fail_item) > 0:
            relog_pathname = fail_path + self.getLogNmae() + "-[fail]-log.txt"
        else:
            relog_pathname = success_path + self.getLogNmae() + "-[pass]-log.txt"

        with open(log_pathname, "r") as rf:
            with open(relog_pathname, "w") as f:
                f.write(rf.read())

        if os.path.exists(log_pathname):
            self.__logger.info(relog_pathname)
            self.__fh.close()
            self.__logger.removeHandler(self.__fh)
            os.remove(log_pathname)

    def MainRun(self, dut_ip):
        # 开始测试
        self.ExecTest(dut_ip)

        # 收集测试结果
        self.CollectResult(self.__col)

        os._exit(0)

    def getLogNmae(self):
        time_str = time.strftime("%Y-%m-%d", time.localtime())
        return "[" + time_str + "]-MAC[" + self.__mac.replace(":", "-") + "]"
