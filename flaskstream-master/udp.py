import socket

class UdpSender:
    def __init__(self, ip_address, ip_port):
        self.host = ip_address
        self.port = ip_port

    def send(self, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message, (self.host, self.port))

class UdpCommandListener:
    def __init__(self, host, port, command_processor):
        self.processor = command_processor
        self.host = host
        self.port = port

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host,self.port))

        while True:
            data, addr = sock.recvfrom(1024)
            result = self.processor.process_udp_command(data)
            if result == "STOP":
                break

