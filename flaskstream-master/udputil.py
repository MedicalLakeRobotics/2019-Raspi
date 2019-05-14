#!/usr/bin/env python3

import sys, getopt
from udp import UdpSender

def main(argv):
    server = "10.45.13.12"
    port = 5800
    msg = "ping"

    try:
        opts, args = getopt.getopt(argv, "hs:p:m:")
    except getopt.GetoptError:
        print ("udputil.py -s <server_hostname_or_ip> -p <server_port> -m <message_to_send>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print ("udputil.py -s <server_hostname_or_ip> -p <server_port> -m <message_to_send>")
            sys.exit(2)
        elif opt == "-s":
            server = arg
        elif opt == "-p":
            port = int(arg)
        elif opt == "-m":
            msg = arg
        else:
            print ("udputil.py -s <server_hostname_or_ip> -p <server_port> -m <message_to_send>")
            sys.exit(2)

    udp = UdpSender(server, port)
    udp.send(msg.encode("utf-8")) 

if __name__ == "__main__":
    main(sys.argv[1:])
