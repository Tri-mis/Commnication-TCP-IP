import time
import math
from threading import Thread, Lock
import socket


DEFAULT_DATA_LENGTH = 10
FORMAT = 'utf-8'

SERVER_IP = "192.168.1.8"
SERVER_PORT = 5050
SERVER_ADDR = (SERVER_IP, SERVER_PORT)

class StructData:
    def __init__ (self, head1, head2, head3, number):
        self.head1 = head1
        self.head2 = head2
        self.head3 = head3
        self.number = number


def data_to_byte(head1, head2, head3, number):
    byte_data = str(head1) + str(head2) + str(head3) + str(number)
    byte_data = byte_data.encode(FORMAT)
    byte_data += b'\0' * (DEFAULT_DATA_LENGTH - len(byte_data))
    return byte_data


def byte_to_struct(byte_data, struct_data):
    byte_data = byte_data.decode('utf-8')
    struct_data.head1 = byte_data[0]
    struct_data.head2 = byte_data[1]
    struct_data.head3 = byte_data[2]

    for i in range(3, len(byte_data)):
        if byte_data[i] == '\0':
            struct_data.number = byte_data[3:i]
            if not struct_data.number:
                break
            struct_data.number = int(struct_data.number)
            break


    
class ClientObject:
    def __init__(self, robot):
        self.client_socket = None
        self.robot = robot
        self.connection = False
        self.struct_data = StructData(0,0,0,0)
        self.stream_flag = 0
        self.send_freq = 100
        self.ack_flag = 0


    def close_socket(self):
        self.client_socket.close()
        print(f"[CLOSE SOCKET]")
        self.connection = False


    def process_data(self, data):
        byte_to_struct(data, self.struct_data)
        match self.struct_data.head1:
            case 'a':
                self.ack_flag = 1
            case 'u':
                self.robot.up_flag = 1
                self.robot.up_req = self.struct_data.number
                self.robot.up = 0
            case 'd':
                self.robot.down_flag = 1
                self.robot.down_req = self.struct_data.number
                self.robot.down = 0
            case 'f':
                self.send_freq = self.struct_data.number
            case 's':
                if self.struct_data.head2 == 'o':
                    self.stream_flag = 1
                if self.struct_data.head2 == 'c':
                    self.stream_flag = 0

        


    def recv_data(self):
        while self.connection:
                data = self.client_socket.recv(DEFAULT_DATA_LENGTH)
                print(f"recv data: {data}")#######
                self.process_data(data)


    def send_data(self):
        pre_time = 0
        while self.connection:

            if self.ack_flag:
                self.client_socket.send(data_to_byte('a', '*', '*', 0))
                self.ack_flag = 0
            
            cur_time = time.time()
            del_time = (cur_time - pre_time) * 1000

            if del_time >= self.send_freq:
                if self.robot.up_flag:
                    self.client_socket.send(data_to_byte('u', '*', '*', self.robot.up))
                    print("sent up")#######
                if self.robot.down_flag:
                    self.client_socket.send(data_to_byte('d', '*', '*', self.robot.down))   
                if self.stream_flag:
                    self.client_socket.send(data_to_byte('s', '*', '*', self.robot.sensor_val))

                pre_time = cur_time

        
    def run(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(SERVER_ADDR)

        print("[CONNECTION] connected to server")

        self.connection = True

        recv_thread = Thread(target = self.recv_data)
        recv_thread.start()
        print("thread started")#########

        send_thread = Thread(target = self.send_data)
        send_thread.start()

        



class Robot:
    def __init__ (self):
        self.up_flag = 0
        self.up = 0
        self.up_req = 0
        self.down_flag = 0
        self.down = 0
        self.down_req = 0
        self.sensor_val = 0


    def move(self):
        while True:
            if self.up_flag:
                if self.up == self.up_req: 
                    self.up_flag = 0
                    continue
                self.up += 1
                print(f"moving up: {self.up}")
            if self.down_flag:
                if self.down == self.up_req: 
                    self.down_flag = 0
                    continue
                self.down += 1
                print(f"moving down: {self.down}")    
            time.sleep(0.5)

    def sensor(self):
        t = 0
        while True:
            self.sensor_val = int(math.cos(2 * math.pi * t) * 100)
            time.sleep(0.05)
            t += 0.05

    def run(self):
        sensor_thread = Thread(target = self.sensor)
        sensor_thread.start()

        move_thread = Thread(target = self.move)
        move_thread.start()


robot1 = Robot()
robot1.run()

client1 = ClientObject(robot1)
client1.run()