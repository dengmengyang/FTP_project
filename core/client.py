import socket
import struct
import json
import os
from config.settings import SERVER_DIR,CLIENT_DIR

class MYTCPClient:
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    allow_reuse_address = False
    max_packet_size = 8192
    coding='gbk'
    request_queue_size = 5

    def __init__(self, server_address, connect=True):
        self.server_address=server_address
        self.socket = socket.socket(self.address_family,
                                    self.socket_type)
        if connect:
            try:
                self.client_connect()
            except:
                self.client_close()
                raise

    def client_connect(self):
        self.socket.connect(self.server_address)

    def client_close(self):
        self.socket.close()

    def run(self):
        while True:
            user = input("请输入用户名：").strip()
            password = input("请输入密码：").strip()
            self.socket.send(struct.pack('i', len(user+' '+password)))
            self.socket.send(bytes(user + ' ' + password, encoding=self.coding))
            login = self.socket.recv(1).decode(self.coding)
            if login == 'Y':
                print('登陆成功')
            else:
                print('登录失败,请重试')
                continue

            while True:
                inp=input("请输入指令>>: ").strip()
                if not inp:continue
                li=inp.split()
                cmd=li[0]

                if hasattr(self,cmd):
                    func=getattr(self,cmd)
                    dic = {'cmd':li[0],'filename':li[1]}
                    func(user, dic)

    @staticmethod
    def progress(percent, width=50):
        #进度条打印
        if percent >= 100:
            percent = 100

        show_str = ('[%%-%ds]' % width) % (int(width * percent / 100) * "#")
        print('\r%s %d%%' % (show_str, percent), end='')

    def put(self,user,kwargs):
        cmd = kwargs['cmd']
        filename = kwargs['filename']
        filepath = CLIENT_DIR + user + '/' + filename
        if not os.path.isfile(filepath):
            print('file:%s is not exists' %filepath)
            return
        else:
            filesize=os.path.getsize(filepath)
            print('文件大小为：',filesize)

        head_dic={'cmd':cmd,'filename':filename,'filepath':filepath,'filesize':filesize}
        #print(head_dic)
        head_json=json.dumps(head_dic)
        head_json_bytes=bytes(head_json,encoding=self.coding)

        head_struct=struct.pack('i',len(head_json_bytes))
        self.socket.send(head_struct)
        self.socket.send(head_json_bytes)
        send_size=0
        with open(filepath,'rb') as f:
            for line in f:
                self.socket.send(line)
                send_size+=len(line)
                send_per = int(100 * send_size / filesize)
                self.progress(send_per)
            else:
                print('upload successful')

    def send_cmd(self,kwargs):
        # 先把cmd发给server
        cmd = kwargs['cmd']
        filename = kwargs['filename']
        cmd_dic = {'cmd': cmd, 'filename': filename}
        #print(cmd_dic)
        cmd_json = json.dumps(cmd_dic)
        cmd_json_bytes = bytes(cmd_json, encoding=self.coding)

        cmd_struct = struct.pack('i', len(cmd_json_bytes))
        self.socket.send(cmd_struct)
        self.socket.send(cmd_json_bytes)

    def get(self,user,kwargs):
        self.send_cmd(kwargs)

        #收head dict
        head_struct = self.socket.recv(4)
        head_len = struct.unpack('i', head_struct)[0]
        head_json = self.socket.recv(head_len).decode(self.coding)
        head_dic = json.loads(head_json)
        #print(head_dic)

        filename = kwargs['filename']
        file_path = os.path.normpath(os.path.join(
            CLIENT_DIR,
            user,
            filename
        ))

        filesize = head_dic['filesize']
        recv_size = 0
        print('----->', file_path)
        with open(file_path, 'wb') as f:
            while recv_size < filesize:
                recv_data = self.socket.recv(self.max_packet_size)
                f.write(recv_data)
                recv_size += len(recv_data)
                recv_per = int(100 * recv_size / filesize)
                self.progress(recv_per)
            else:
                print("接收成功")

    def ls(self,user,kwargs):
        self.send_cmd(kwargs)

        path_struct = self.socket.recv(4)
        path_len = struct.unpack('i', path_struct)[0]
        path_json = self.socket.recv(path_len).decode(self.coding)
        path_list = json.loads(path_json)
        print(path_list)



