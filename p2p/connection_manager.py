from concurrent.futures import ThreadPoolExecutor
import socket
import threading
import pickle

from .core_node_list import CoreNodeList
from .edge_node_list import EdgeNodeList

from p2p.message_manager import (
        MessageManager,
        MSG_ADD,
        MSG_REMOVE,
        MSG_CORE_LIST,
        MSG_REQUEST_CORE_LIST,
        MSG_PING,
        MSG_ADD_AS_EDGE,
        MSG_REMOVE_EDGE,

        ERR_PROTOCOL_UNMATCH,
        ERR_VERSION_UNMATCH,
        OK_WITH_PAYLOAD,
        OK_WITHOUT_PAYLOAD,
        )

PING_INTERVAL = 1800 # 30分

class ConnectionManager:
    def __init__(self, host, my_port, callback):
        print('Initializeing ConnectionManager...')
        print(f'self.host: {host}')
        print(f'self.my_port: {my_port}')
        self.my_c_host = None
        self.my_c_port = None
        self.host = host
        self.port = my_port
        self.core_node_set = CoreNodeList()
        self.edge_node_set = EdgeNodeList()
        self.__add_peer((host, my_port))
        self.mm = MessageManager()
        self.callback = callback

    # 受付開始処理 
    def start(self):
        t = threading.Thread(target=self.__wait_for_access)
        t.start()

        self.ping_timer = threading.Timer(PING_INTERVAL, self.__check_peers_connection)
        self.ping_timer.start()

    # ユーザーが指定した既知のCoreノードへの接続(ServerCore向け)
    def join_network(self, host, port):
        self.my_c_host = host
        self.my_c_port = port
        self.__connect_to_P2PNW(host, port)

    def get_message_text(self, msg_type, payload = None):
        """
        指定したメッセージ種別のプロトコルメッセージを作成して返却する
        
        params:
            msg_type : 作成したいメッセージの種別をMessageManagerの規定に従い指定
            payload : メッセージにデータを格納したい場合に指定する
        
        return:
            msgtxt : MessageManagerのbuild_messageによって生成されたJSON形式のメッセージ
        """
        msgtxt = self.mm.build(msg_type, self.port, payload)
        print('generated_msg:', msgtxt)
        return msgtxt

    # 指定されたノードへ対してメッセージを送信する
    def send_msg(self, peer, msg):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer))
            s.sendall(msg.encode('utf-8'))
            s.close()
        except OSError:
            print('Connection fialed for peer :', peer)
            self.__remove_peer(peer)

    # Coreノードリストに登録されているすべてのノードに対して同じメッセージをブロードキャストする
    def send_msg_to_all_peer(self, msg):
        print('send_msg_to_all_peer was called!')
        for peer in self.core_node_set.get_list():
            if peer != (self.host, self.port):
                print('message will be sent to ...', peer)
                self.send_msg(peer, msg)

    # Edgeノードリストに登録されている全てのノードに対して同じメッセージをブロードキャストする
    def send_msg_to_all_edge(self, msg):
        print('send_msg_to_all_edge was called! ')
        current_list = self.edge_node_set.get_list()
        for edge in current_list:
            print("message will be sent to ... " ,edge)
            self.send_msg(edge, msg)

    # 終了前の処理としてソケットを閉じる
    def connection_close(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        self.socket.close()
        s.close()
        # 接続確認のスレッドの停止
        self.ping_timer.cancel()
        print(self.my_c_host)
        # 離脱要求の送信
        if self.my_c_host is not None:
            msg = self.mm.build(MSG_REMOVE, self.port)
            self.send_msg((self.my_c_host, self.my_c_port), msg)

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
                if cmd == MSG_ADD:
                    print('ADD node request was received!!')
                    self.__add_peer((addr[0], peer_port))
                    if (addr[0], peer_port) == (self.host, self.port):
                        return
                    else:
                        cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
                        msg = self.mm.build(MSG_CORE_LIST, self.port, cl)
                        self.send_msg_to_all_peer(msg)
                elif cmd == MSG_REMOVE:
                    print('REMOVE request was received!! from', addr[0], peer_port)
                    self.__remove_peer((addr[0], peer_port))
                    cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
                    msg = self.mm.build(MSG_CORE_LIST, self.port, cl)
                    self.send_msg_to_all_peer(msg)
                elif cmd == MSG_ADD_AS_EDGE:
                    print('MSG_ADD_AS_EDGE!! from', addr[0], peer_port)
                    self.__add_edge_node((addr[0], peer_port))
                    cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
                    msg = self.mm.build(MSG_CORE_LIST, self.port, cl)
                    self.send_msg((addr[0], peer_port), msg)
                elif cmd == MSG_REMOVE_EDGE:
                    self.__remove_edge_noge((addr[0], peer_port))
                elif cmd == MSG_PING:
                    # 今は特にやることなし
                    return
                elif cmd == MSG_REQUEST_CORE_LIST:
                    print('List for Core nodes was requested!!')
                    cl = pickle.dumps(self.core_node_set.get_list(), 0).decode()
                    msg = self.mm.build(MSG_CORE_LIST, self.port, cl)
                    self.send_msg((addr[0], peer_port), msg)
                else:
                    print('received unknown command', cmd)
                    return
            elif status == ('ok', OK_WITH_PAYLOAD):
                if cmd == MSG_CORE_LIST:
                    # TODO: 受信したリストをただ上書きしてしまうのはセキュリティ的に良くはない
                    # 信頼できるノード鍵などを使って検証する仕組みをいれるべき
                    print('Refresh the core node list...')
                    new_core_set = pickle.loads(payload.encode('utf-8'))
                    print('latest core node list:', new_core_set)
                    self.core_node_set.overwrite(new_core_set)
                else:
                    self.callback((result, reason, cmd, peer_port, payload), None)
                    return
            else:
                print('Unecxpected status: ', status)
        except:
            import traceback
            traceback.print_exc()


    # 新たに接続されたCoreノードをリストに追加する
    def __add_peer(self, peer):
        self.core_node_set.add((peer))
      
    # 離脱したCoreノードをリストから削除する
    def __remove_peer(self, peer):
        self.core_node_set.remove(peer)

    # 接続されているCoreノードすべての接続状況確認を行う
    def __check_peers_connection(self):
        """
        接続されているCoreノードすべての接続状況確認をおこなう
        クラス外からは利用しない
        定期実行される
        """
        print('check_peers_connection was called')
        current_core_list = self.core_node_set.get_list()
        changed = False
        deag_c_node_set = list(filter(lambda p: not self.__is_alive(p), current_core_list))
        if deag_c_node_set:
            changed = True
            print('Removing ', deag_c_node_set)
            current_core_list = current_core_list - set(deag_c_node_set)
            self.core_node_set.overwrite(current_core_list)

        current_core_list = self.core_node_set.get_list()
        print('current core node list:', current_core_list)
        # 変更があったときだけブロードキャストで通知する
        if changed:
            cl = pickle.dumps(current_core_list, 0).decode()
            msg = self.mm.build(MSG_CORE_LIST, self.port, cl)
            self.send_msg_to_all_peer(msg)

        self.ping_timer = threading.Timer(PING_INTERVAL, self.__check_peers_connection)
        self.ping_timer.start()

    """
    有効ノード確認メッセージの送信

    param:
        target: 有効ノード確認メッセージの送り先となるノードの接続情報(IPとポート)
    """
    def __is_alive(self, target):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target))
            msg_type = MSG_PING
            msg = self.mm.build(msg_type)
            s.sendall(msg.encode('utf-8'))
            s.close()
            return True
        except OSError:
            return False

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
                import traceback
                traceback.print_exc()
                print(e)
                break

    def __connect_to_P2PNW(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        msg = self.mm.build(MSG_ADD, self.port)
        s.sendall(msg.encode('utf-8'))
        s.close()

    def __add_edge_node(self, edge):
        """
        Edgeノードをリストに追加する
        """
        print("__add_edge_node")
        self.edge_node_set.add((edge))

    def __remove_edge_noge(self, edge):
        """
        離脱したと判断されるEdgeノードをリストから削除する。
        """
        self.edge_node_set.remove(edge)
