# import sys, time, subprocess
# import os, datetime, operator

# class PingNetwork:
#     def __init__(self, cfg, logger, language):
#         self.__cfg = cfg
#         self.__logger = logger
#         self.__zh_cn = language
#         self.__conn_succ = False
#         self.__Ping_stop = False
#         self.__ping_result_file = "ping.temp"
        
#         if os.path.exists(self.__ping_result_file):
#             os.remove(self.__ping_result_file)

#     def PingManyTimes(self, ip, times):
#         for i in range(int(times)):
#             time.sleep(0.5)
#             if self.PingDut(ip) == False:
#                 continue
#             else:
#                 return True

#         return False

#     def PingDut(self, ip):
#         # 判断操作系统
#         if operator.eq(sys.platform, "linux"):
#             times = '-c'
#         elif operator.eq(sys.platform, "win32"):
#             times = '-n'
#         else:
#             times = '-n'

#         self.__logger.info(self.__zh_cn("ping_info"), ip)

#         cmd = "ping " + times + " 1 " + ip + " -w 1"
#         PingProcess = subprocess.Popen(cmd, stdout=open(self.__ping_result_file, 'w'), stderr=open(self.__ping_result_file, 'w'), shell=True)
#         PPres = PingProcess.wait()
#         PingProcess.kill()

#         if PPres == 0:
#             self.__logger.info(self.__zh_cn("check_success"))
#             return True
#         else:
#             self.__logger.error(self.__zh_cn("check_fail"))
#             return False

# from https://github.com/corentone/python3-ping
import os
import sys
import socket
import struct
import select
import time

if sys.platform == "win32":
    # On Windows, the best timer is time.clock()
    default_timer = time.time
else:
    # On most other platforms the best timer is time.time()
    default_timer = time.time

# From /usr/include/linux/icmp.h; your milage may vary.
ICMP_ECHO_REQUEST = 8 # Seems to be the same on Solaris.

class PingNetwork(object):
    def __init__(self, cfg, logger, language):
        self.__cfg = cfg
        self.__logger = logger
        self.__zh_cn = language

    def checksum(self, source_string):
        """
        I'm not too confident that this is right but testing seems
        to suggest that it gives the same answers as in_cksum in ping.c
        """
        sum = 0
        countTo = (len(source_string)/2)*2
        count = 0
        while count<countTo:
            thisVal = source_string[count + 1]*256 + source_string[count]
            sum = sum + thisVal
            sum = sum & 0xffffffff # Necessary?
            count = count + 2

        if countTo<len(source_string):
            sum = sum + source_string[len(source_string) - 1]
            sum = sum & 0xffffffff # Necessary?

        sum = (sum >> 16)  +  (sum & 0xffff)
        sum = sum + (sum >> 16)
        answer = ~sum
        answer = answer & 0xffff

        # Swap bytes. Bugger me if I know why.
        answer = answer >> 8 | (answer << 8 & 0xff00)

        return answer


    def receive_one_ping(self, my_socket, ID, timeout):
        """
        receive the ping from the socket.
        """
        timeLeft = timeout
        while True:
            startedSelect = default_timer()
            whatReady = select.select([my_socket], [], [], timeLeft)
            howLongInSelect = (default_timer() - startedSelect)
            if whatReady[0] == []: # Timeout
                return

            timeReceived = default_timer()
            recPacket, addr = my_socket.recvfrom(1024)
            icmpHeader = recPacket[20:28]
            type, code, checksum, packetID, sequence = struct.unpack(
                "bbHHh", icmpHeader
            )
            # Filters out the echo request itself.
            # This can be tested by pinging 127.0.0.1
            # You'll see your own request
            if type != 8 and packetID == ID:
                bytesInDouble = struct.calcsize("d")
                timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
                return timeReceived - timeSent

            timeLeft = timeLeft - howLongInSelect
            if timeLeft <= 0:
                return


    def send_one_ping(self, my_socket, dest_addr, ID):
        """
        Send one ping to the given >dest_addr<.
        """
        dest_addr  =  socket.gethostbyname(dest_addr)

        # Header is type (8), code (8), checksum (16), id (16), sequence (16)
        my_checksum = 0

        # Make a dummy heder with a 0 checksum.
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
        bytesInDouble = struct.calcsize("d")
        data = bytes((192 - bytesInDouble) * "Q", 'utf-8')
        data = struct.pack("d", default_timer()) + data

        # Calculate the checksum on the data and the dummy header.
        my_checksum = self.checksum(header + data)

        # Now that we have the right checksum, we put that in. It's just easier
        # to make up a new header than to stuff it into the dummy.
        header = struct.pack(
            "bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
        )
        packet = header + data
        my_socket.sendto(packet, (dest_addr, 1)) # Don't know about the 1


    def do_one(self, dest_addr, timeout):
        """
        Returns either the delay (in seconds) or none on timeout.
        """
        icmp = socket.getprotobyname("icmp")
        try:
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        except PermissionError as e:
            e.args = (e.args if e.args else tuple()) + ((
                " - Note that ICMP messages can only be sent from processes"
                " running as root."
            ),)
            raise

        my_ID = os.getpid() & 0xFFFF

        self.send_one_ping(my_socket, dest_addr, my_ID)
        delay = self.receive_one_ping(my_socket, my_ID, timeout)

        my_socket.close()
        return delay


    def PingManyTimes(self, dest_addr, count, timeout=1):
        """
        Send >count< ping to >dest_addr< with the given >timeout< and display
        the result.
        """
        for __ in range(count):
            self.__logger.info("ping %s..." % dest_addr)
            try:
                delay  =  self.do_one(dest_addr, timeout)
            except socket.gaierror as e:
                self.__logger.info("failed. (socket error: '%s')" % e)
                break

            if delay is None:
                self.__logger.info("failed. (timeout within %ssec.)" % timeout)
                continue
            else:
                delay = delay * 1000
                self.__logger.info("get ping in %0.4fms" % delay)
                return True

        return False
