from concurrent.futures import ThreadPoolExecutor
import socket
import threading
import pickle

from .core_node_list import CoreNodeList
from p2p.message_manager import (
        MessageManager,
        MSG_CORE_LIST,
        MSG_PING,
        MSG_ADD_AS_EDGE,
        ERR_PROTOCOL_UNMATCH,
        ERR_VERSION_UNMATCH,
        OK_WITH_PAYLOAD,
        OK_WITHOUT_PAYLOAD,
        )

#PING_INTERVAL = 1800 # 30分
PING_INTERVAL = 10 # for デバッグ

class ConnectionManager4Edge(object):
    def __init__(self, host, my_port, my_core_host, my_core_port, callback):
        print('Initializeing ConnectionManager4Edge...')
        print(f'self.host: {host}')
        print(f'self.my_port: {my_port}')
        print(f'self.my_core_host: {my_core_host}')
        print(f'self.my_core_port: {my_core_port}')
        self.my_c_host = None
        self.my_c_port = None
        self.host = host
        self.port = my_port
        self.my_core_host = my_core_host
        self.my_core_port = my_core_port
        self.core_node_set = CoreNodeList()
        self.mm = MessageManager()
        self.callback = callback

    # 受付開始処理 
    def start(self):
        t = threading.Thread(target=self.__wait_for_access)
        t.start()

        self.ping_timer = threading.Timer(PING_INTERVAL, self.__send_ping)
        self.ping_timer.start()

    def connect_to_core_node(self):
        """
        ユーザが指定した既知のCoreノードへの接続
        """
        self.__connect_to_P2PNW(self.my_core_host, self.my_core_port)

    # 指定されたノードへ対してメッセージを送信する
    def send_msg(self, peer, msg):
        print(f"Sending... {msg}")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer))
            s.sendall(msg.encode('utf-8'))
            s.close()
        except:
            print('Connection fialed for peer :', peer)
            self.core_node_set.remove(peer)
            print('Tring to connect into P2P network...')
            current_core_list = self.core_node_set.get_list()
            # 接続エラー時は他のノードへ接続し直す
            if len(current_core_list) != 0:
                new_core = self.core_node_set.get_c_node_info()
                self.my_core_host = new_core[0]
                self.my_core_port = new_core[1]
                self.connect_to_core_node()
                self.send_msg((new_core[0], new_core[1]), msg)
            else:
                print("No core node found in our list...")
                self.ping_timer.cancel()

    # 終了前の処理としてソケットを閉じる
    def connection_close(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        self.socket.close()
        s.close()
        # 接続確認のスレッドの停止
        self.ping_timer.cancel()

    def get_message_text(self, msg_type, payload = None):
        msgtxt = self.mm.build(msg_type, self.port, payload)
        return msgtxt

    def __connect_to_P2PNW(self, host, port):
        """
        指定したCoreノードへ接続要求メッセージを送信する
        """
        print("connect_to_P2PNW")
        print(f"host #{host}")
        print(f"port #{port}")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        msg = self.mm.build(MSG_ADD_AS_EDGE, self.port)
        print(msg)
        s.sendall(msg.encode('utf-8'))
        s.close()

    def __wait_for_access(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(0)

        executor = ThreadPoolExecutor(max_workers=10)

        while True:
            try:
                print('Waiting for the connection...')
                soc, addr = self.socket.accept()
                print('Connected by ..', addr)
                data_sum = ''

                params = (soc, addr, data_sum)
                executor.submit(self.__handle_message, params)
            except Exception as e:
                print(e)
                break


    # 受信したメッセージを確認して、内容に応じた処理を行う(private)
    def __handle_message(self, params):
        try:
            soc, addr, data_sum = params

            while True:
                data = soc.recv(1024)
                data_sum = data_sum + data.decode('utf-8')

                if not data:
                    break

            if not data_sum:
                return

            result, reason, cmd, peer_port, payload = self.mm.parse(data_sum)
            print(result, reason, cmd, peer_port, payload)
            status = (result, reason)
            if status == ('error', ERR_PROTOCOL_UNMATCH):
                print('Error: Protocol name is not matched')
                return
            elif status == ('error', ERR_VERSION_UNMATCH):
                print('Error: Protocol version is not matched')
            elif status == ('ok', OK_WITHOUT_PAYLOAD):
                # PING以外のメッセージはEdgeノードでは受け取らない
                if cmd == MSG_PING:
                    pass
                else:
                    print('received unknown command', cmd)
                    return
            elif status == ('ok', OK_WITH_PAYLOAD):
                if cmd == MSG_CORE_LIST:
                    # Coreノード情報の受け取りを行う
                    print('Refresh the core node list...')
                    new_core_set = pickle.loads(payload.encode('utf-8'))
                    print('latest core node list:', new_core_set)
                    self.core_node_set.overwrite(new_core_set)
                else:
                    print('received unknown command', cmd)
                    self.callback((result, reason, cmd, peer_port, payload))
                    return
            else:
                print('Unecxpected status: ', status)
        except:
            import traceback
            traceback.print_exc()

    def __send_ping(self):
        """
        接続状況確認メッセージ送信
        """
        peer = (self.my_core_host, self.my_core_port)

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer))
            msg = self.mm.build(MSG_PING)
            s.sendall(msg.encode('utf-8'))
            s.close()
        except:
            print('Connection fialed for peer :', peer)
            self.core_node_set.remove(peer)
            print('Tring to connect into P2P network...')
            current_core_list = self.core_node_set.get_list()
            # 接続エラー時は他のノードへ接続し直す
            if len(current_core_list) != 0:
                new_core = self.core_node_set.get_c_node_info()
                self.my_core_host = new_core[0]
                self.my_core_port = new_core[1]
                self.connect_to_core_node()
                self.send_msg((new_core[0], new_core[1]), msg)
            else:
                print("No core node found in our list...")
                self.ping_timer.cancel()

        self.ping_timer = threading.Timer(PING_INTERVAL, self.__send_ping)
        self.ping_timer.start()

    def __add_edge_node(self, edge):
        """
        Edgeノードをリストに追加する
        """
        self.edge_node_set.add((edge))

    def __remove_edge_noge(self, edge):
        """
        離脱したと判断されるEdgeノードをリストから削除する。
        """
        self.edge_node_set.remove(edge)
