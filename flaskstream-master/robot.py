import time
import os
import sys
import subprocess
import threading
import yaml
from udp import UdpCommandListener
from udp import UdpSender
from camera import RobotCamera

class Robot:

    def __init__(self):
        self.front_camera = None
        self.rear_camera = None
        self.live_camera = None
        self.udp_listener_thread = None
        self.frame_lag = 0.02
        self.jpeg_quality = 40
        self.udp_inbound_command_port = 5800
        self.udp_outbound_host = "10.45.13.2"
        self.udp_outbound_port = 5801
        self.udp_sender = None
        self.take_snapshot_now = True #take a snap on startup
        self.target_path_bearing = None
        self.flip_image = False

    def startup(self):
        self._setup()
        if self.front_camera is None:
            self.live_camera = self.rear_camera
        else:
            self.live_camera = self.front_camera
        self.init_udp_thread()

    def init_udp_thread(self):
        if self.udp_listener_thread is None:
            self.udp_listener_thread = threading.Thread(target=self.listen_on_udp)
            print("starting thread")
            self.udp_listener_thread.start()

    def listen_on_udp(self):
        udp = UdpCommandListener("0.0.0.0", self.udp_inbound_command_port, self)
        print("listening to udp")
        udp.start()

    def send_udp_message_to_robot(self, message):
        self.udp_sender.send(message.encode("utf-8"))

    def process_udp_command(self, data):
        cmds = data.decode("utf-8").upper().split()
        if len(cmds) == 0:
            return "OK"
        cmd = cmds.pop(0)
        print("UDP received command: {}".format(cmd))
        if cmd == "FRONT" and not self.front_camera is None:
            self.live_camera = self.front_camera
        elif cmd == "REAR" and not self.rear_camera is None:
            self.live_camera = self.rear_camera
        elif cmd == "SNAPSHOT":
            self.take_snapshot_now = True
        elif cmd == "BEARING":
            self.target_path_bearing = int(cmds.pop(0))
        elif cmd == "FLIP":
            if self.flip_image == True:
                self.flip_image = False
            else:
                self.flip_image = True
        return "OK"

    def send_stats_to_robot(self, stats, camera):
        msg = self._format_stats_message(stats, camera)
        self.send_udp_message_to_robot(msg)

    #private methods
    def _format_stats_message(self, stats, camera):
        if stats[0] == False:
            stats_string = "0"
        else:
            stats_string = "1 {} {} {} {} {} {}".format(stats[1], stats[2], stats[3], stats[4], stats[5], stats[6])
        return "{} {} {}".format(camera.role, stats_string, time.clock())

    def _setup(self):
        camera_defs, view_def = self._load_cameras_from_yaml()
        camera_devices = self._load_camera_devices()
        print(camera_devices)
        print(view_def)
        self.jpeg_quality = view_def["jpeg_quality"]
        self.frame_lag = view_def["frame_lag"]
        self.udp_inbound_command_port = view_def["udp_inbound_command_port"]
        self.udp_outbound_host = view_def["udp_outbound_host"]
        self.udp_outbound_port = view_def["udp_outbound_port"]
        self.udp_sender = UdpSender(self.udp_outbound_host, self.udp_outbound_port)

        self.front_camera = self._find_camera("front", camera_defs, camera_devices, view_def)
        self.rear_camera = self._find_camera("rear", camera_defs, camera_devices, view_def)

        if self.front_camera is None and self.rear_camera is None:
            keys = list(camera_devices.keys())
            key_count = len(keys)
            if key_count > 0:
                self.front_camera = self._find_camera_by_serial(keys[0], "front", camera_defs, camera_devices, view_def)
            if key_count > 1:
                self.rear_camera = self._find_camera_by_serial(keys[1], "rear", camera_defs, camera_devices, view_def)

    def _load_cameras_from_yaml(self):
        with open(os.path.join(sys.path[0], "config.yml"), 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            print(cfg['cameras'])
            return cfg['cameras'], cfg['camera_view']

    def _find_camera(self, key, camera_defs, devices, view):
        serial_number = str(camera_defs[key]["serial"])
        return self._find_camera_by_serial(serial_number, key, camera_defs, devices, view)

    def _find_camera_by_serial(self, serial_number, role, camera_defs, devices, view):
        device = devices.get(serial_number, None)
        if device == None:
            return None
        else:
            ndx = device["device_name"][-1]
            camera = RobotCamera(self, device["device_name"], ndx, role, serial_number)
            camera.width = view["width"]
            camera.height = view["height"]
            camera.fps = view["fps"]
            camera.start_streaming()
            return camera

    def _load_camera_devices(self):
        devices = {}
        for i in range(0,6):
            device_name = "/dev/video{}".format(str(i))
            serial_number = self._value_from_udev(device_name, "ID_SERIAL_SHORT")
            if len(serial_number) > 2:
                devices[serial_number] = {"device_name": device_name, "serial_number": serial_number}
        return devices

    def _value_from_udev(self, device_name, key):
        cmd = "udevadm info --query=property {} | grep {}".format(device_name, key)
        value = ""
        try:
            value = subprocess.check_output(cmd, shell = True)
            value = value.decode().strip().split("=")[1]
        except:
            return ""
        return value

