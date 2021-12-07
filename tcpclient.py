# data sender

# input format
# tcpclient file address_of_udpl port_number_of_udpl windowsize ack_port_number

import array
import random
import socket
import struct
import sys

from bitarray import bitarray
from bitarray.util import ba2int

class TCPPacket:
    # TCP SEGMENT STRUCTURE
    def __init__(self, src_port, dst_port, window_size, data):
        self.src_port = src_port                    # 16 bits
        self.dst_port = dst_port                    # 16 bits
        self.seq_num = 0                            # 32 bits
        self.ack_num = 0                            # 32 bits
        self.data_offset = 5                        # 4 bits - 20 bytes, 5 words
        self.reserved_field = 0                      # 3 bits
        self.flag_ns = 0                             # 1 bit - ignore
        self.flag_cwr = 0                            # 1 bit - ignore
        self.flag_ece = 0                            # 1 bit - ignore
        self.flag_urg = 0                            # 1 bit - ignore
        self.flag_ack = 0                            # 1 bit
        self.flag_psh = 0                            # 1 bit - ignore
        self.flag_rst = 0                            # 1 bit - ignore
        self.flag_syn = 0                            # 1 bit
        self.flag_fin = 0                             # 1 bit
        self.window_size = window_size              # 16 bits
        self.checksum = 0                           # 16 bits
        self.urg_pointer = 0                        # 16 bits
        self.data = data
        self.state = ""

    def buildPacket(self) -> bytes:
        # the packet should be exactly 20 bytes
        packet = struct.pack(
            'HHIIHHH',
            int(self.src_port),      # Source Port
            int(self.dst_port),      # Destination Port
            self.seq_num,            # Sequence Number
            self.ack_num,            # ACK Number
            int(self.window_size),   # Window
            self.checksum,           # Checksum (init)
            self.urg_pointer         # Urgent pointer
        )

        # compose 16 bits using header_length(offset),
        #                       reserve_field and flags
        self.data_offset = bitarray('{0:04b}'.format(self.data_offset))
        self.reserved_field = bitarray('{0:03b}'.format(self.reserved_field))
        flags = bitarray([
            self.flag_ns,
            self.flag_cwr,
            self.flag_ece,
            self.flag_urg,
            self.flag_ack,
            self.flag_psh,
            self.flag_rst,
            self.flag_syn,
            self.flag_fin
        ])
        offset_flags = self.data_offset + self.reserved_field + flags

        # convert to integer and pack into tcp header as bytes
        offset_flag_int = ba2int(offset_flags)
        offset_flags_byte = struct.pack(
            'H',
            offset_flag_int
        )
        packet = packet[:12] + offset_flags_byte + packet[12:]

        # compute checksum based on the header and data
        real_checksum = self.checkSum(packet + bytes(self.data))
        header = packet[:16] + struct.pack('H', real_checksum) + packet[18:]

        return header

    # Computed over TCP header and data
    def checkSum(self, packet):
        if len(packet) % 2 != 0:
            packet += b'\0'

        res = sum(array.array("H", packet))
        res = (res >> 16) + (res & 0xffff)
        res += res >> 16

        return (~res) & 0xffff


    def updateState(self):
        if self.flag_syn == 1 and self.flag_ack == 1:
            self.state = "SYN-ACK"
        elif self.flag_ack == 1 and self.flag_fin == 1:
            self.state = "FIN-ACK"
        elif self.flag_syn == 1:
            self.state = "SYN"
        elif self.flag_ack == 1:
            self.state = "ACK"
        elif self.flag_fin == 1:
            self.state = "FIN"
        elif self.data != "":
            self.state = "DATA"
        return


    def updateFlag(self, ack=False, syn=False, fin=False):
        self.flag_ack = 1 if ack else 0
        self.flag_syn = 1 if syn else 0
        self.flag_fin = 1 if fin else 0
        return


def sendPacket(argv):
    file_name = argv[1]
    file_bytes = bytes(readFiles(file_name))

    addr_udpl = argv[2]    # dest_address
    port_udpl = argv[3]    # dest_port
    window_size = argv[4]
    port_ack = argv[5]

    packet = TCPPacket(port_ack, port_udpl, window_size, file_bytes)
    header = packet.buildPacket()
    packet = header + file_bytes

    UDP_IP = "localhost"
    UDP_PORT = 12000
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM)  # UDP

    # sock.bind((UDP_IP, UDP_PORT))
    # sock.sendto(packet, addr_udpl)

    sock.sendto(packet, (UDP_IP, UDP_PORT))

# retransmission_time = datetime.timedelta(seconds=3) # adjust per TCP standard
# seg_size = 576

# read binary data from a file
def readFiles(file_name):
    file_bytes = bytearray()
    try:
        with open(file_name, "rb") as f:
            file_bytes += f.read()
    except IOError:
        print("Did not find the file under correct directory!")
    return file_bytes


if __name__ == "__main__":
    # print(sys.argv)
    sendPacket(sys.argv)