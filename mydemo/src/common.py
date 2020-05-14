import glob
import sys
import threading
import time
import os
import re
import operator
import socket
import paramiko
import hashlib
import json
import visa
from .connect import *

CELL_PARA_NAME = "cell_para.json"
FILE_PATH = "./file/"
CELL_PARA_PATHNAME = FILE_PATH + CELL_PARA_NAME

class common(connect):
    def __init__(self, cfg, logger, ping_thread, language, col, path):
        super().__init__(cfg, logger, ping_thread, language, col, path)
        self.__cfg = cfg
        self.__logger = logger
        self.__ping_thread = ping_thread
        self.__zh_cn = language
        self.__col = col
        self.__path = path

        self.tips = "---"
        self.ping_max_time = 5
        self.reset_wait_time = 80
        self.test_success_item_result = {}
        self.test_fail_item = {}
        self.nchp_no = []
        self.ncho_reset_pin = []
        self.cell_start_time = 0
        self.cell_sw = ""

        self.external_gain = self.__cfg.get("common", "external_gain")
        
        self.test_item_name = [
            "power_calibration",
        ]

    def resToNvram(self, item, res):
        self.test_success_item_result[item] = res

    def resToDict(self, check_item, dict, res, tips=""):
        print_item = self.tips + " " + check_item
        self.test_success_item_result[print_item] = res + tips

        for k, v in dict.items():
            self.resToNvram(k, v)
            self.__logger.info(v)

    def saveRes(self, status, item_name, dict, tips=""):
        if status > 0:
            self.test_fail_item[item_name] = self.__zh_cn(item_name)
            self.__col.setPrintRed()
            self.__logger.error(self.__zh_cn("check_fail") + tips)
            self.__col.resetColor()
            self.resToDict(self.__zh_cn(item_name), dict,
                           self.__zh_cn("check_fail"), tips)
            return False
        else:
            self.__col.setPrintGreen()
            self.__logger.info(self.__zh_cn("check_success") + tips)
            self.__col.resetColor()
            self.resToDict(self.__zh_cn(item_name), dict,
                           self.__zh_cn("check_success"), tips)
            return True

    def get_model(self, ip):
        cmd = "/usr/sbin/aptool getintmodel"
        ret = self.cmdLastField(ip, cmd)
        model = re.findall(r"Internal Model: ([0-9A-Z]*-[0-9A-Z]*)", ret)
        self.__logger.info("model: %s" % model[0])
        return model[0]

    # 获取命令执行结果的最后一个字段
    def cmdLastField(self, ip, cmd, get_pty=True):
        ret = self.SSHExecCmd(ip, cmd, get_pty=get_pty)
        self.__logger.debug(ret)
        # print(ret)
        return ret

    def file_is_exist(self, ip, filename):
        cmd = "find " + filename
        file_is_exist = self.cmdLastField(ip, cmd)

        if operator.eq(file_is_exist, filename):
            return True
        else:
            return False

    def wait_time(self, wait_time):
        for i in range(0, wait_time):
            time.sleep(1)
            print("\r Waitting... " + str(i) + " to " + str(wait_time), end="")
        print("")

    def switch_cell(self, ip, nchp_no, sw):
        if operator.eq(sw, "on"):
            sw = "on"
            gpio_sw = "high"
        else:
            sw = "off"
            gpio_sw = "low"

        self.cell_sw = sw

        self.__logger.info("cell " + sw + " %s" % str(nchp_no))
        cmd = "/usr/sbin/pctl setcellstatus " + str(nchp_no) + " " + sw
        self.SSHExecCmd(ip, cmd, get_pty=False)

        # 开启/关闭fdd功放
        if int(nchp_no) == 1 or int(nchp_no) == 2:
            gpio = str(int(nchp_no) + 11)
            cmd = "/usr/sbin/gpioexp status " + gpio + " " + gpio_sw
            self.cmdLastField(ip, cmd)
            self.__logger.info("gpioexp " + gpio + " Power amplifier " + sw)

    def read_json_file(self, pathname: str) -> list:
        res_list = {}

        with open(pathname, "r") as f:
            res_list = json.load(f)

        return res_list

    def write_json_file(self, pathname: str, conf: list) -> int:
        with open(pathname, "w") as f:
            f.write(json.dumps(conf, indent=4))

    def nchp_cmd(self, chan, cmd: str):
        ret = self.SSHInvokeShell(chan, cmd)
        # print(ret)
        return ret

    def login_nchp(self, ip: str, nchp_no: int):
        # ssh交互进入信道板
        chan = self.SSHInvokeShellInit(ip)

        nchp_ip = "192.254.4." + str(90+int(nchp_no))

        self.__logger.info("login %s" % nchp_ip)

        for __ in range(2):
            cmd = "/usr/sbin/ssh root@" + nchp_ip
            ret = self.SSHInvokeShell(chan, cmd, timeout=2)
            # print(ret)
            if "y/n" in ret:
                ret = self.SSHInvokeShell(chan, "y")
                # print(ret)
                if "password" in ret:
                    ret = self.SSHInvokeShell(chan, "root123")
                    ret = self.SSHInvokeShell(chan, "pwd")
                    if "root@OpenWrt" in ret:
                        return chan

        raise RuntimeError("login nchp failed")

    def logout_nchp(self, chan):
        self.SSHInvokeShellClose(chan)

    def connect_SA(self, ip: str):
        VISA_ADDRESS = "TCPIP0::" + ip + "::5025::SOCKET"

        resourceManager = visa.ResourceManager()
        session = resourceManager.open_resource(VISA_ADDRESS)

        if session.resource_name.startswith('ASRL') or session.resource_name.endswith('SOCKET'):
            session.read_termination = '\n'

        session.write('*IDN?')
        idn = session.read()

        ret = idn.rstrip('\n')
        # 支持的信号分析仪
        support_sa = "N9020A"
        if not support_sa in ret:
            raise ValueError("Just support devices: N9020A")

        # 设置通信超时时间
        session.set_visa_attribute(visa.constants.VI_ATTR_TMO_VALUE, 10000)

        # 复位
        session.write(':SYST:PRES;')

        return resourceManager, session

    def disconnect_SA(self, resourceManager, session):
        session.close()
        resourceManager.close()

    def wait_for_cell_on(self, ip, nchp_no, gsm=0):
        self.__logger.info(self.__zh_cn("wait_for_cell"))
        wh_times = 0
        while (1):
            cmd = "/usr/sbin/pctl getcellinfo | grep \"192.254.4." + \
                str(nchp_no+90+gsm) + "\" | grep -Eo \"state:([A-Z]*),\""
            ret = self.cmdLastField(ip, cmd)
            if "WORK" in ret:
                break
            else:
                if wh_times > 300:
                    raise ValueError("CELL ABNORMAL")

            wh_times += 1
            time.sleep(1)
            print("\r Waitting... " + str(wh_times), end="")
        print("")
        self.__logger.info("OK")

    def power_calibration(self, ip):
        self.__logger.info(self.__zh_cn("start_power_calibration"))
        power_calibration = {}
        power_calibration_status = 0

        nchp_ant = []
        nchp_ant_old = []

        try:

            self.__plat_name = self.get_model(ip)

            lte_num = self.__cfg[self.__plat_name]["lte_total"]
            gsm_num = self.__cfg[self.__plat_name]["gsm_total"]

            self.carrier_power = int(self.__cfg[self.__plat_name]["target_power"])
            self.carrier_power_offset = int(self.__cfg[self.__plat_name]["target_power_offset"])

            resourceManager, session = self.connect_SA(self.__cfg["dut"]["sa_ip"])

            if int(lte_num) > 0:
                # 遍历天线
                for ant_no in range(2):
                    tmp = "ant" + str(ant_no+1) + "_total_rounds"
                    total_rounds = self.__cfg[self.__plat_name][tmp]

                    input(self.__zh_cn("change_ant") % str(ant_no + 1))

                    # 遍历每根天线测试轮数
                    for round_no in range(int(total_rounds)):
                        self.__logger.info(self.__zh_cn("start_round") % str(round_no + 1))
                        tmp = "ant" + str(ant_no+1) + "_round_" + str(round_no+1) + "_band"
                        round_band = self.__cfg[self.__plat_name][tmp].strip().split(',')

                        # 各天线求band对应的频点
                        tmp = "ant" + str(ant_no+1) + "_round_" + str(round_no+1) + "_arfcn"
                        nchp_arfcn = self.__cfg[self.__plat_name][tmp].strip().split(',')

                        self.__logger.info("ant_no: %s, round_no: %s, arfcn: %s" % (ant_no+1, round_no+1, str(nchp_arfcn)))

                        cell_para_list = []
                        cell_no = 0
                        # 遍历每轮测试各小区的band
                        if len(round_band) != int(lte_num):
                            raise ValueError(self.__logger.info(self.__zh_cn("conf_error")))

                        self.__logger.info(self.__zh_cn("fill_conf"))
                        for nchp_no in range(len(round_band)):
                            # 填充小区配置文件
                            if 0 != int(nchp_arfcn[nchp_no]) and 0 != int(nchp_arfcn[nchp_no]):
                                cell_para_list.append({})
                                cell_para_list[cell_no]["cellNo"] = nchp_no
                                cell_para_list[cell_no]["rat"] = 1
                                cell_para_list[cell_no]["arfcn"] = int(nchp_arfcn[nchp_no])
                                cell_para_list[cell_no]["pci"] = 500
                                cell_para_list[cell_no]["tac"] = 10001
                                cell_para_list[cell_no]["tacIncreasePeriod"] = 1800
                                cell_para_list[cell_no]["freqBand"] = int(round_band[nchp_no])
                                cell_para_list[cell_no]["mnc"] = 0
                                cell_para_list[cell_no]["syncMode"] = 1
                                cell_para_list[cell_no]["powerLevel"] = 20
                                cell_para_list[cell_no]["onOff"] = 0
                                # cell_para_list[cell_no]["minTac"] = 10000
                                # cell_para_list[cell_no]["maxTac"] = 20000
                                # cell_para_list[cell_no]["rejectReason"] = 15
                                # cell_para_list[cell_no]["bandWidth"] = 5
                                # cell_para_list[cell_no]["tmDelay"] = 100000

                                cell_no += 1

                        self.write_json_file(CELL_PARA_PATHNAME, cell_para_list)

                        # 上传到主控板
                        cmd = "/usr/bin/tftp -g -l /tmp/" + CELL_PARA_NAME + " -r " + CELL_PARA_NAME + " " + self.getData("local_ip")
                        ret = self.cmdLastField(ip, cmd)
                        if "timeout" in ret:
                            raise TimeoutError("tftp server not open")
                        elif "File not found" in ret:
                            raise ValueError("tftp /tmp/" + CELL_PARA_NAME + " not found")
                        if self.file_is_exist(ip, "/tmp/" + CELL_PARA_NAME) == False:
                            raise ValueError("tftp /tmp/" + CELL_PARA_NAME + " not found")

                        # 执行 pctl setcelldefconfig 配置小区参数
                        self.__logger.info(self.__zh_cn("set_cell_conf_ok"))
                        cmd = "/usr/sbin/pctl setcelldefconfig /tmp/" + CELL_PARA_NAME
                        self.SSHExecCmd(ip, cmd, get_pty=False)
                        self.wait_time(5)

                        # 开小区
                        self.__logger.info(self.__zh_cn("start_cell"))
                        for nchp_no in range(len(round_band)):
                            if 0 != int(round_band[nchp_no]) and 0 != int(nchp_arfcn[nchp_no]):
                                self.switch_cell(ip, nchp_no, "on")

                        # 获取ad9391寄存器值
                        tmp1 = "ant" + str(ant_no+1) + "_round_" + str(round_no+1) + "_ant"
                        nchp_ant = self.__cfg[self.__plat_name][tmp1].strip().split(',')

                        # 信道板天线口不一致则重启
                        if len(nchp_ant_old) > 0:
                            for nchp_ant_no in range(len(nchp_ant)):
                                if int(nchp_ant[nchp_ant_no]) != 0 and int(nchp_ant_old[nchp_ant_no]) != 0 \
                                        and int(nchp_ant[nchp_ant_no]) != int(nchp_ant_old[nchp_ant_no]):
                                    # 重启信道板
                                    self.__logger.info(self.__zh_cn("reboot_nchp"))
                                    cmd = "/usr/sbin/pctl reboot-nchp"
                                    self.SSHExecCmd(ip, cmd, get_pty=False)
                                    break

                        nchp_ant_old = nchp_ant

                        for nchp_no in range(len(round_band)):
                            if 0 != int(round_band[nchp_no]) and 0 != int(nchp_arfcn[nchp_no]):
                                self.wait_for_cell_on(ip, nchp_no)

                                # 登录nchp
                                chan = self.login_nchp(ip, nchp_no)
                                self.__logger.info(self.__zh_cn("init_sa"))
                                # 选择lte
                                session.write('INSTrument:SELect LTE')
                                # 初始化acp
                                session.write('INITiate:ACP')
                                # 设置参考
                                session.write('DISP:ACP:VIEW:WIND:TRAC:Y:RLEV 35')
                                # 设置频点、带宽
                                tmp = "freq_lte_" + nchp_arfcn[nchp_no]
                                center_freq = self.__cfg["common"][tmp]
                                session.write('FREQuency:CENTer %sMHZ' % center_freq)
                                session.write('SENSe:RADio:STAN:PRES B5M')
                                # 设置衰减
                                session.write('SENSe:CORRection:BTS:GAIN ' + self.external_gain)

                                try:
                                    for get_value_times in range(3):
                                        # 获取ad9391寄存器值
                                        tmp2 = "nchp_ant" + nchp_ant[nchp_no] + "_reg"
                                        reg = self.__cfg["common"][tmp2]
                                        ad9361_cmd = "/root/ad9361 " + reg + " "
                                        ret = self.nchp_cmd(chan, ad9361_cmd)
                                        reg_value_before = re.findall(r"value:0x([0-9a-fA-F]*)", ret)
                                        reg_value_before = int(reg_value_before[0], 16)
                                        self.__logger.info("ad9391 %s: %s" % (reg , hex(int(reg_value_before))))

                                        # 判断小区是否开
                                        if reg_value_before > 96:
                                            self.wait_time(10)
                                            if get_value_times >= 2:
                                                raise ValueError("CELL " + str(nchp_no) + ": band: " + \
                                                    str(round_band[nchp_no]) + ": arfcn: " + str(nchp_arfcn[nchp_no]) + \
                                                    ": NOT ON: reg " + str(reg) + " value: " + hex(int(reg_value_before)))
                                        else:
                                            break
                                except ValueError as e:
                                    power_calibration_status += 1
                                    power_calibration["CELL_ERR"] = str(e)
                                    self.__logger.error(str(e))
                                    continue

                                # 获取bandRfCfg.xml中该band的配置值
                                tmp = "lte_band" + round_band[nchp_no] + "_line"
                                band_line = self.__cfg["common"][tmp]
                                cmd = "sed -n \"" + band_line + "p\" /intel/bandRfCfg.xml"
                                ret = self.nchp_cmd(chan, cmd)
                                conf_value_before = re.findall(r"<txAttInDb> ([0-9]*)</txAttInDb>", ret)
                                conf_value_before = int(conf_value_before[0])
                                self.__logger.info("conf_value_before: %d" % conf_value_before)

                                # 测量acp
                                power = 0
                                power_upper = int(self.carrier_power) + int(self.carrier_power_offset)
                                power_lower = int(self.carrier_power) - int(self.carrier_power_offset)

                                reg_value = reg_value_before
                                # 各小区 acpl
                                tmp = "ant" + str(ant_no+1) + "_round_" + str(round_no+1) + "_acpl"
                                nchp_acpl = self.__cfg[self.__plat_name][tmp].strip().split(',')

                                ca_times = 0
                                flag = 0
                                power = 0
                                try:
                                    while 1:
                                        time.sleep(1)
                                        ret = session.query_ascii_values(':READ:ACP?')
                                        power = ret[1]
                                        left_acpl = ret[4]
                                        right_apcl = ret[6]
                                        self.__logger.info(self.__zh_cn( "carrier power: ") + str(power))
                                        self.__logger.info(self.__zh_cn("left acpl: ") + str(left_acpl))
                                        self.__logger.info(self.__zh_cn("right apcl: ") + str(right_apcl))

                                        if float(right_apcl) < float(nchp_acpl[nchp_no]) and float(right_apcl) < float(nchp_acpl[nchp_no]):
                                            if power > power_upper:
                                                flag = 0
                                            elif power < power_lower:
                                                flag = 1
                                            else:
                                                break
                                        else:
                                            flag = 0

                                        if 0 == flag:
                                            reg_value += 4
                                            cmd = ad9361_cmd + str(hex(reg_value))
                                            self.nchp_cmd(chan, cmd)
                                        else:
                                            reg_value -= 4
                                            cmd = ad9361_cmd + str(hex(reg_value))
                                            self.nchp_cmd(chan, cmd)

                                        if ca_times > 10:
                                            raise RuntimeError(
                                                "Calibration Failed")
                                        ca_times += 1
                                except RuntimeError as e:
                                    power_calibration_status += 1
                                    power_calibration["CELL_Calibration"] = str(e)
                                    self.__logger.error(str(e))
                                    continue

                                power_calibration["Lte" + str(nchp_no) + "_Bnad" + str(round_band[nchp_no]) +
                                                  "_" + str(nchp_arfcn[nchp_no])] = "Power: " + str(power)

                                # 写入配置文件
                                try:
                                    self.__logger.info("reg_value_before: %d, reg_value: %d" % (reg_value_before, reg_value))
                                    conf_value = 0
                                    if reg_value != reg_value_before:
                                        conf_value = int(conf_value_before - (reg_value_before - reg_value)/4)
                                        if conf_value > 0:
                                            self.__logger.info("conf_value_before: %d, conf_value: %d" % (conf_value_before, conf_value))
                                            cmd = "sed -i \"" + band_line + "s/" + str(conf_value_before) + "/" + \
                                                    str(conf_value) + "/g\" /intel/bandRfCfg.xml"
                                            self.nchp_cmd(chan, cmd)
                                        else:
                                            raise ValueError(self.__logger.info(self.__zh_cn("conf_power_value_error") + str(conf_value)))

                                    if int(round_band[nchp_no]) == 38:
                                        cmd = "sed -n \"" + self.__cfg["common"]["lte_band41_line"] + "p\" /intel/bandRfCfg.xml"
                                        ret = self.nchp_cmd(chan, cmd)
                                        conf_value_before_41 = re.findall(r"<txAttInDb> ([0-9]*)</txAttInDb>", ret)
                                        conf_value_before_41 = int(conf_value_before_41[0])

                                        if conf_value_before != conf_value_before_41 or conf_value != 0:
                                            if conf_value == 0:
                                                conf_value = reg_value_before
                                            
                                            self.__logger.info("conf_value_before_41: %d, conf_value: %d" % (conf_value_before_41, conf_value))
                                            cmd = "sed -i \"" + self.__cfg["common"]["lte_band41_line"] + "s/" + str(
                                                conf_value_before_41) + "/" + str(conf_value) + "/g\" /intel/bandRfCfg.xml"
                                            self.nchp_cmd(chan, cmd)

                                except ValueError as e:
                                    power_calibration_status += 1
                                    power_calibration["Write_to_file"] = str(e)
                                    self.__logger.error(str(e))
                                    continue
                                self.logout_nchp(chan)
                        # 关小区
                        self.__logger.info("ant %s ok" % str(ant_no+1))
                        for nchp_no in range(len(round_band)):
                            if 0 != int(nchp_arfcn[nchp_no]) and 0 != int(nchp_arfcn[nchp_no]):
                                self.switch_cell(ip, nchp_no, "off")

                        self.__logger.info("round %s ok" % round_no)

                    self.__logger.info("ant %s ok" % str(ant_no+1))

            if int(gsm_num) > 0:
                input(self.__zh_cn("change_gsm_ant"))

                gsm_arfcn = self.__cfg[self.__plat_name]["total_arfcn"].strip().split(',')

                self.__logger.info("gsm_arfcn: %s" % str(gsm_arfcn))

                if len(gsm_arfcn) != int(gsm_num):
                    raise ValueError(self.__logger.info(
                        self.__zh_cn("conf_error")))

                cell_para_list = []
                cell_no = 0
                for nchp_no in range(len(gsm_arfcn)):
                    # 填充小区配置文件
                    if 0 != int(gsm_arfcn[nchp_no]) and 0 != int(gsm_arfcn[nchp_no]):
                        cell_para_list.append({})
                        cell_para_list[cell_no]["cellNo"] = nchp_no
                        cell_para_list[cell_no]["rat"] = 6
                        cell_para_list[cell_no]["arfcn"] = int(gsm_arfcn[nchp_no])
                        cell_para_list[cell_no]["tacIncreasePeriod"] = 600
                        cell_para_list[cell_no]["powerLevel"] = 30
                        cell_para_list[cell_no]["gsmBcc"] = 5
                        cell_para_list[cell_no]["gsmNcc"] = 8
                        cell_para_list[cell_no]["gsmReselOffset"] = 0
                        cell_para_list[cell_no]["onOff"] = 0
                        cell_para_list[cell_no]["pci"] = 500
                        cell_para_list[cell_no]["tac"] = 1000

                        cell_no += 1

                self.write_json_file(CELL_PARA_PATHNAME, cell_para_list)

                # 上传到主控板
                cmd = "/usr/bin/tftp -g -l /tmp/" + CELL_PARA_NAME + " -r " + CELL_PARA_NAME + " " + self.getData("local_ip")
                ret = self.cmdLastField(ip, cmd)
                if "timeout" in ret:
                    raise TimeoutError("tftp server not open")
                elif "File not found" in ret:
                    raise ValueError("tftp /tmp/" + CELL_PARA_NAME + " not found")
                if self.file_is_exist(ip, "/tmp/" + CELL_PARA_NAME) == False:
                    raise ValueError("tftp /tmp/" + CELL_PARA_NAME + " not found")

                # 执行 pctl setcelldefconfig 配置小区参数
                self.__logger.info(self.__zh_cn("set_cell_conf_ok"))
                cmd = "/usr/sbin/pctl setcelldefconfig /tmp/" + CELL_PARA_NAME
                self.SSHExecCmd(ip, cmd, get_pty=False)

                # 开小区
                self.switch_cell(ip, int(lte_num), "on")

                for nchp_no in range(len(gsm_arfcn)):
                    self.wait_for_cell_on(ip, 0, gsm=9)

                    # 登录nchp
                    chan = self.login_nchp(ip, 9 + int(nchp_no))

                    self.__logger.info(self.__zh_cn("init_sa"))
                    # 选择lte
                    session.write('INSTrument:SELect LTE')
                    # 初始化acp
                    session.write('INITiate:ACP')
                    # 设置参考
                    session.write('DISP:ACP:VIEW:WIND:TRAC:Y:RLEV 35')
                    # 设置频点、带宽
                    tmp = "freq_gsm_" + gsm_arfcn[nchp_no]
                    center_freq = self.__cfg["common"][tmp]
                    session.write('FREQuency:CENTer %sMHZ' % center_freq)
                    session.write('SENSe:RADio:STAN:PRES B5M')
                    # 设置衰减
                    session.write('SENSe:CORRection:BTS:GAIN ' + self.external_gain)

                    # 获取bandRfCfg.xml中该band的配置值
                    band_line = self.__cfg["common"]["gsm_line"]
                    cmd = "sed -n \"" + band_line + "p\" /intel/rfPortCfg.xml"
                    ret = self.nchp_cmd(chan, cmd)
                    conf_value_before = re.findall(r"<txAttnu> ([0-9]*)</txAttnu>", ret)
                    conf_value_before = int(conf_value_before[0])
                    self.__logger.info("conf_value_before: %d" % conf_value_before)

                    try:
                        for get_value_times in range(3):
                            ret = session.query_ascii_values(':READ:ACP?')
                            power = ret[1]
                            self.__logger.info(self.__zh_cn("carrier power: ") + str(power))

                            if power > 0:
                                break
                            if get_value_times >= 2:
                                raise ValueError(self.__logger.info(self.__zh_cn("conf_power_value_error") + str(conf_value)))
                            self.wait_time(10)

                        # 写入配置文件
                        conf_value = int(conf_value_before + (int(power) - int(self.carrier_power)))
                        if conf_value != conf_value_before:
                            if conf_value > 0:
                                self.__logger.info("conf_value_before: %d, conf_value: %d" % (
                                    conf_value_before, conf_value))
                                cmd = "sed -i \"" + band_line + "s/" + str(conf_value_before) + "/" + \
                                    str(conf_value) + "/g\" /intel/rfPortCfg.xml"
                                self.nchp_cmd(chan, cmd)
                            else:
                                raise ValueError(self.__logger.info(self.__zh_cn("conf_power_value_error") + str(conf_value)))
                    except ValueError as e:
                        power_calibration_status += 1
                        power_calibration["Write_to_file"] = str(e)
                        self.__logger.error(str(e))
                        continue

                    power_calibration["Gsm" + str(nchp_no) +
                                      "_" + str(gsm_arfcn[nchp_no])] = "Power: " + str(power)

                    self.logout_nchp(chan)

                # 开小区
                self.switch_cell(ip, int(lte_num), "off")

            self.disconnect_SA(resourceManager, session)

        except IndexError as e:
            power_calibration_status += 1
            power_calibration["IndexError"] = str(e)
            self.__logger.error(str(e))
        except ValueError as e:
            power_calibration_status += 1
            power_calibration["ValueError"] = str(e)
            self.__logger.error(str(e))
        except RuntimeError as e:
            power_calibration_status += 1
            power_calibration["RuntimeError"] = str(e)
            self.__logger.error(str(e))
        except KeyError as e:
            power_calibration_status += 1
            power_calibration[self.__zh_cn("not_support_dev")] = str(e)
            self.__logger.error(str(e))
        except TimeoutError as e:
            power_calibration_status += 1
            power_calibration[self.__zh_cn("tftp_server_not_open")] = str(e)
            self.__logger.error(str(e))
        else:
            pass

        if power_calibration_status > 0 and self.cell_sw == "on":
            # 关小区
            for nchp_no in range(int(lte_num) + int(int(gsm_num)/2)):
                self.switch_cell(ip, nchp_no, "off")

        return self.saveRes(power_calibration_status, sys._getframe().f_code.co_name, power_calibration)

    def DoTest(self, test_item, dut_ip):
        # 主控版ip
        ip_mcb = dut_ip

        # 功率校准
        if operator.eq(test_item, "power_calibration"):
            return self.power_calibration(ip_mcb)
        else:
            return False

    def GetSupportTestItem(self):
        return self.test_item_name
