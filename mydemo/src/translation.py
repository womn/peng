class translation(object):
    def __init__(self):
        self.translation_dict = {}
        self.initTransDict()

    def GetTranslation(self, word):
        if word in self.translation_dict:
            return self.translation_dict[word]
        return word

    def initTransDict(self):
        self.translation_dict = {
            # 配置相关
            "miss_config_file": "缺少配置文件：",
            "exectest_err": "配置错误：[test_step] 仅支持 ManualTest、AutoTest",
            "tx_rx_conf_err": "band、ant配置错误",
            "log_file": "log文件：",
            "input_mac": "   请输入设备MAC：",

            "testd": "  已测试通过，跳过",
            "testd_fail": "重新测试所有项按 'y', 继续测试失败项目按'f': ",

            # ping相关
            "ping_info": "Ping目标设备 [%s]",
            "ping_fail": "Ping失败, 请检查链路",

            # tftp相关
            "tftp_port_occupied": "TFTP服务已被其他程序占用，请关闭其他TFTP服务程序",
            "tftp_success": "TFTP服务建立成功：[%s]",
            "tftp_lack_path": "缺少tftp目录：",

            # 连接相关
            "start": "测试开始",
            "start_connect_telnet": "开始telnet连接目标设备 [%s:%s]",
            "connect_break": "与设备连接断开",
            "connect_fail": "连接异常:",
            "start_connect_ssh": "开始ssh连接目标设备 [%s:%s]",
            "read_line_timeout": "读取ssh行：超时",
            "used_time": "测试共用时：",

            # 检测相关
            "check_success": "成功",
            "check_fail": "失败",
            "start_collect_result": "==================== 测试结果 ====================",
            "start_collect_fail_item": "==================== 失败项目 ====================",
            "end_collect_result": "==================================================",
            "dont_support_item": "不支持测试项目：",

            # 版本检测
            "version_check": "版本检测",
            "start_version_check": "开始检测版本",
            "mcb_version_err": "主控版本[%s]与目标版本[%s]不一致, 开始升级",
            "nchp_version_err": "信道板版本[%s]与目标版本[%s]不一致",
            "start_update": "开始升级",

            # U盘检测
            "disk_check": "U盘检测",
            "start_disk_check": "开始检测U盘",

            # RTC设置
            "rtc_set": "RTC设置",
            "start_rtc_set": "开始设置RTC",

            # LED灯检测
            "led_check": "LED灯检测",
            "start_led_check": "开始检测信道板LED灯，请观察LED闪烁",
            "led_info": "LED灯闪烁正常输入“y”，失败输入“n”， 重新观察输入“r”",

            # 温度检测
            "temperature_check": "温度检测",
            "start_temperature_check": "开始检测温度",

            # GPS检测
            "gps_check": "GPS检测",
            "start_gps_check": "开始检测GPS",

            # WiFi检测
            "wifi_check": "WiFi检测",
            "start_wifi_check": "开始检测WiFi",
            "wifi_info": "请使用 WirelessMon软件 查看并输入 wifi: %s Rssi信号强度: ",
            "wifi_input_error": "输入有误请重新输入: ",

            # 3G拨号检测
            "network_3g_check": "3G拨号检测",
            "start_network_3g_check": "开始检测3G拨号",
            "reset_lte": "复位lte",
            "init_lte": "初始化lte",
            "set_apn_lte": "设置apn",
            "only_3g_lte": "设置仅3G拨号",
            "check_sim_lte": "检查sim卡",
            "connect_lte": "拨号",
            "link_status_lte": "链路状态正常",
        
            # LTE扫频检测
            "scanfreq_check": "扫频检测",

            # LTE扫频检测
            "scanfreq_lte_check": "LTE扫频检测",
            "start_scanfreq_lte_check": "开始检测LTE扫频",

            # GSM扫频检测
            "scanfreq_gsm_check": "GSM扫频检测",
            "start_scanfreq_gsm_check": "开始检测GSM扫频",

            # LTE、GSM制式检测
            "cell_module_check": "LTE、GSM制式检测",
            "start_cell_module_check": "开始检测LTE、GSM制式",
        
            # 信道板复位检测
            "nchp_reset": "信道板复位检测",
            "start_nchp_reset": "开始检测信道板复位",
            "nchp_reset_sleep": "等待信道板重启",

            # 1pps信号检测
            "check_1pps": "1pps信号检测",
            "start_check_1pps": "开始检测1pps信号",
            
            # 空口同步
            "air_sync_check": "空口同步检测",
            "start_air_sync_check": "开始检测空口同步",

            # 上号检测
            "value_check": "上号检测",
            "start_value_check": "开始检测上号",

            # 导入默认小区配置
            "import_cell_defconfig": "导入默认小区配置",
            "start_import_cell_defconfig": "开始导入默认小区配置",

            # 导入oem
            "import_oem": "导入oem",
            "start_import_oem": "开始导入oem",
            "input_oem_company": "请输入oem company: ",

            # 掉电告警
            "power_warn": "掉电告警检测",
            "start_power_warn": "开始检测掉电告警",
            "power_warn_info": "请在%s秒内断掉设备电源",

            # 主控主备版本是否一致检查
            "flash_mcb_version": "主控主备版本是否一致检查",
            "start_flash_mcb_version": "开始检查主控主备版本是否一致",
            
            # 设置TDD为空口同步
            "set_tdd_air_sync": "设置TDD为空口同步",
            "start_set_tdd_air_sync": "开始设置TDD为空口同步",

            # 检查factory_env
            "factory_env_check": "检查factory_env",
            "start_factory_env_check": "开始检查factory_env",

            # 功率校准
            "power_calibration": "功率校准",
            "start_power_calibration": "开始校准功率",
            "init_sa": "初始化仪表",
            "set_cell_conf_ok": "设置小区参数OK",
            "change_ant": "======> 请更换天线至天线%s，安装完成后请输入'y' : ",
            "change_gsm_ant": "======> 请更换天线至GSM天线，安装完成后请输入'y' : ",
            "power": "功率: ",
            "conf_power_value_error": "写入功率参数有误: ",
            "conf_error": "配置文件有误",
            "start_round": "开始测试第%s轮: ",
            "fill_conf": "开始生成小区参数配置文件:",
            "reboot_nchp": "重启所有信道板",
            "start_cell": "开小区: ",
            "wait_for_cell": "等待小区启动",
            "not_support_dev": "不支持的设备: ",
            "tftp_server_not_open": "tftp服务未打开",

        }
