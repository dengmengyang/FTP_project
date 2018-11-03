import socket
import struct
import json
import subprocess
import os,sys
import configparser
from config.settings import SERVER_DIR,CONFIG_FILE

class MYTCPServer:
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    allow_reuse_address = False
    max_packet_size = 8192
    coding='gbk'
    request_queue_size = 5

    def __init__(self, server_address, bind_and_activate=True):
        """Constructor.  May be extended, do not override."""
        self.server_address = server_address
        self.socket = socket.socket(self.address_family,
                                    self.socket_type)
        if bind_and_activate:
            try:
                self.server_bind()
                self.server_activate()
            except:
                self.server_close()
                raise

    def server_bind(self):
        """Called by constructor to bind the socket.
        """
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()

    def server_activate(self):
        """Called by constructor to activate the server.
        """
        self.socket.listen(self.request_queue_size)

    def server_close(self):
        """Called to clean-up the server.
        """
        self.socket.close()

    def get_request(self):
        """Get the request and client address from the socket.
        """
        return self.socket.accept()

    def close_request(self, request):
        """Called to clean up an individual request."""
        request.close()

    def login_access(self):
        while True:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            user_list = config.sections()
            user_struct = self.conn.recv(4)
            user_len = struct.unpack('i', user_struct)[0]
            user_pass = self.conn.recv(user_len).decode(self.coding)
            if not user_pass: break
            user = user_pass.split()[0]
            password = user_pass.split()[1]

            if ((user in user_list) and (str(password)==config[user]['password'])):
                self.conn.send(bytes('Y',encoding=self.coding))
                return user
            else:
                self.conn.send(bytes('N',encoding=self.coding))
                return

    @staticmethod
    def progress(percent, width=50):
        #进度打印
        if percent >= 100:
            percent = 100

        show_str = ('[%%-%ds]' % width) % (int(width * percent / 100) * "#")
        print('\r%s %d%%' % (show_str, percent), end='')

    def run(self):
        while True:
            self.conn,self.client_addr=self.get_request()
            print('from client ',self.client_addr)
            while True:
                try:
                    user = self.login_access()
                    if user:
                        print("用户%s 登陆成功"%user)

                    else: continue

                    while True:
                        head_struct = self.conn.recv(4)
                        if not head_struct: break
                        head_len = struct.unpack('i', head_struct)[0]
                        head_json = self.conn.recv(head_len).decode(self.coding)
                        head_dic = json.loads(head_json)
                        #print(head_dic)
                        # head_dic={'cmd':'put','filename':'a.txt','filesize':123123}
                        cmd = head_dic['cmd']
                        if hasattr(self, cmd):
                            func = getattr(self, cmd)
                            func(user,head_dic)
                except Exception:
                    break

    def put(self,user,kwargs):
        file_path = os.path.normpath(os.path.join(
            SERVER_DIR,
            user,
            kwargs['filename']
        ))
        print("上传路径为：",file_path)

        filesize = kwargs['filesize']
        recv_size = 0
        print('----->', file_path)
        with open(file_path, 'wb') as f:
            while recv_size < filesize:
                recv_data = self.conn.recv(self.max_packet_size)
                if not recv_data:
                    print('没有接收到内容！')
                    return
                f.write(recv_data)
                recv_size += len(recv_data)
                recv_per = int(100 * recv_size / filesize)
                self.progress(recv_per)
            else:
                print("接受成功")

    def get(self,user,kwargs):
        cmd = kwargs['cmd']
        filename = kwargs['filename']
        filepath = SERVER_DIR + user + '/'+filename
        if not os.path.isfile(filepath):
            print('file:%s is not exists' % filepath)
            return
        else:
            filesize = os.path.getsize(filepath)

        head_dic = {'cmd': cmd, 'filename': filename,'filepath':filepath, 'filesize': filesize}
        #print(head_dic)
        head_json = json.dumps(head_dic)
        head_json_bytes = bytes(head_json, encoding=self.coding)

        head_struct = struct.pack('i', len(head_json_bytes))
        self.conn.send(head_struct)
        self.conn.send(head_json_bytes)
        send_size = 0
        with open(filepath, 'rb') as f:
            for line in f:
                self.conn.send(line)
                send_size += len(line)
                send_per = int(100 * send_size / filesize)
                self.progress(send_per)
            else:
                print('传输成功！')

    def ls(self,user,kwargs):
        cmd = kwargs['cmd']
        file = kwargs['filename']
        path = SERVER_DIR+user+kwargs['filename']
        if os.path.exists(path):
            file_list = os.listdir(path)
            path_json = json.dumps(file_list)
            path_json_bytes = bytes(path_json, encoding=self.coding)
        else:
            print("文件夹不存在")
            path_json = json.dumps("路径不存在")
            path_json_bytes = bytes(path_json, encoding=self.coding)

        path_struct = struct.pack('i', len(path_json))
        self.conn.send(path_struct)
        self.conn.send(path_json_bytes)
        return


